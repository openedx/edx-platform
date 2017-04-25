"""
APIs providing support for enterprise functionality.
"""
from functools import wraps
import hashlib
import logging
import six

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from slumber.exceptions import HttpClientError, HttpServerError

from edx_rest_api_client.client import EdxRestApiClient
try:
    from enterprise import utils as enterprise_utils
    from enterprise.models import EnterpriseCourseEnrollment
    from enterprise.utils import consent_necessary_for_course
except ImportError:
    pass
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from slumber.exceptions import SlumberBaseException
from requests.exceptions import ConnectionError, Timeout
from openedx.core.djangoapps.api_admin.utils import course_discovery_api_client

from openedx.core.lib.token_utils import JwtBuilder


CONSENT_FAILED_PARAMETER = 'consent_failed'
ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS = 'enterprise_customer_branding_override_details'
LOGGER = logging.getLogger("edx.enterprise_helpers")


class EnterpriseApiException(Exception):
    """
    Exception for errors while communicating with the Enterprise service API.
    """
    pass


class EnterpriseApiClient(object):
    """
    Class for producing an Enterprise service API client.
    """

    def __init__(self):
        """
        Initialize an Enterprise service API client, authenticated using the Enterprise worker username.
        """
        self.user = User.objects.get(username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME)
        jwt = JwtBuilder(self.user).build_token([])
        self.client = EdxRestApiClient(
            configuration_helpers.get_value('ENTERPRISE_API_URL', settings.ENTERPRISE_API_URL),
            jwt=jwt
        )

    def post_enterprise_course_enrollment(self, username, course_id, consent_granted):
        """
        Create an EnterpriseCourseEnrollment by using the corresponding serializer (for validation).
        """
        data = {
            'username': username,
            'course_id': course_id,
            'consent_granted': consent_granted,
        }
        endpoint = getattr(self.client, 'enterprise-course-enrollment')  # pylint: disable=literal-used-as-attribute
        try:
            endpoint.post(data=data)
        except (HttpClientError, HttpServerError):
            message = (
                "An error occured while posting EnterpriseCourseEnrollment for user {username} and "
                "course run {course_id} (consent_granted value: {consent_granted})"
            ).format(
                username=username,
                course_id=course_id,
                consent_granted=consent_granted,
            )
            LOGGER.exception(message)
            raise EnterpriseApiException(message)

    def fetch_enterprise_learner_data(self, site, user):
        """
        Fetch information related to enterprise from the Enterprise Service.

        Example:
            fetch_enterprise_learner_data(site, user)

        Argument:
            site: (Site) site instance
            user: (User) django auth user

        Returns:
            dict: {
                "enterprise_api_response_for_learner": {
                    "count": 1,
                    "num_pages": 1,
                    "current_page": 1,
                    "results": [
                        {
                            "enterprise_customer": {
                                "uuid": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                "name": "TestShib",
                                "catalog": 2,
                                "active": true,
                                "site": {
                                    "domain": "example.com",
                                    "name": "example.com"
                                },
                                "enable_data_sharing_consent": true,
                                "enforce_data_sharing_consent": "at_login",
                                "enterprise_customer_users": [
                                    1
                                ],
                                "branding_configuration": {
                                    "enterprise_customer": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                    "logo": "https://open.edx.org/sites/all/themes/edx_open/logo.png"
                                },
                                "enterprise_customer_entitlements": [
                                    {
                                        "enterprise_customer": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                        "entitlement_id": 69
                                    }
                                ]
                            },
                            "user_id": 5,
                            "user": {
                                "username": "staff",
                                "first_name": "",
                                "last_name": "",
                                "email": "staff@example.com",
                                "is_staff": true,
                                "is_active": true,
                                "date_joined": "2016-09-01T19:18:26.026495Z"
                            },
                            "data_sharing_consent": [
                                {
                                    "user": 1,
                                    "state": "enabled",
                                    "enabled": true
                                }
                            ]
                        }
                    ],
                    "next": null,
                    "start": 0,
                    "previous": null
                }
            }

        Raises:
            ConnectionError: requests exception "ConnectionError", raised if if ecommerce is unable to connect
                to enterprise api server.
            SlumberBaseException: base slumber exception "SlumberBaseException", raised if API response contains
                http error status like 4xx, 5xx etc.
            Timeout: requests exception "Timeout", raised if enterprise API is taking too long for returning
                a response. This exception is raised for both connection timeout and read timeout.

        """
        api_resource_name = 'enterprise-learner'

        cache_key = get_cache_key(
            site_domain=site.domain,
            resource=api_resource_name,
            username=user.username
        )

        response = cache.get(cache_key)
        if not response:
            try:
                endpoint = getattr(self.client, api_resource_name)
                querystring = {'username': user.username}
                response = endpoint().get(**querystring)
                cache.set(cache_key, response, settings.ENTERPRISE_API_CACHE_TIMEOUT)
            except (HttpClientError, HttpServerError):
                message = ("An error occurred while getting EnterpriseLearner data for user {username}".format(
                    username=user.username
                ))
                LOGGER.exception(message)
                return None

        return response


def data_sharing_consent_required(view_func):
    """
    Decorator which makes a view method redirect to the Data Sharing Consent form if:

    * The wrapped method is passed request, course_id as the first two arguments.
    * Enterprise integration is enabled
    * Data sharing consent is required before accessing this course view.
    * The request.user has not yet given data sharing consent for this course.

    After granting consent, the user will be redirected back to the original request.path.

    """
    @wraps(view_func)
    def inner(request, course_id, *args, **kwargs):
        """
        Redirect to the consent page if the request.user must consent to data sharing before viewing course_id.

        Otherwise, just call the wrapped view function.
        """
        # Redirect to the consent URL, if consent is required.
        consent_url = get_enterprise_consent_url(request, course_id)
        if consent_url:
            real_user = getattr(request.user, 'real_user', request.user)
            LOGGER.warning(
                u'User %s cannot access the course %s because they have not granted consent',
                real_user,
                course_id,
            )
            return redirect(consent_url)

        # Otherwise, drop through to wrapped view
        return view_func(request, course_id, *args, **kwargs)

    return inner


def enterprise_enabled():
    """
    Determines whether the Enterprise app is installed
    """
    return 'enterprise' in settings.INSTALLED_APPS and getattr(settings, 'ENABLE_ENTERPRISE_INTEGRATION', True)


def consent_needed_for_course(user, course_id):
    """
    Wrap the enterprise app check to determine if the user needs to grant
    data sharing permissions before accessing a course.
    """
    if not enterprise_enabled():
        return False
    return consent_necessary_for_course(user, course_id)


def get_enterprise_consent_url(request, course_id, user=None, return_to=None):
    """
    Build a URL to redirect the user to the Enterprise app to provide data sharing
    consent for a specific course ID.

    Arguments:
    * request: Request object
    * course_id: Course key/identifier string.
    * user: user to check for consent. If None, uses request.user
    * return_to: url name label for the page to return to after consent is granted.
                 If None, return to request.path instead.
    """
    if user is None:
        user = request.user

    if not consent_needed_for_course(user, course_id):
        return None

    if return_to is None:
        return_path = request.path
    else:
        return_path = reverse(return_to, args=(course_id,))

    url_params = {
        'course_id': course_id,
        'next': request.build_absolute_uri(return_path),
        'failure_url': request.build_absolute_uri(
            reverse('dashboard') + '?' + urlencode(
                {
                    CONSENT_FAILED_PARAMETER: course_id
                }
            )
        ),
    }
    querystring = urlencode(url_params)
    full_url = reverse('grant_data_sharing_permissions') + '?' + querystring
    LOGGER.info('Redirecting to %s to complete data sharing consent', full_url)
    return full_url


def insert_enterprise_pipeline_elements(pipeline):
    """
    If the enterprise app is enabled, insert additional elements into the
    pipeline so that data sharing consent views are used.
    """
    if not enterprise_enabled():
        return

    additional_elements = (
        'enterprise.tpa_pipeline.handle_enterprise_logistration',
    )
    # Find the item we need to insert the data sharing consent elements before
    insert_point = pipeline.index('social.pipeline.social_auth.load_extra_data')

    for index, element in enumerate(additional_elements):
        pipeline.insert(insert_point + index, element)


def get_enterprise_customer_logo_url(request):
    """
    Client API operation adapter/wrapper.
    """

    if not enterprise_enabled():
        return None

    parameter = get_enterprise_branding_filter_param(request)
    if not parameter:
        return None

    provider_id = parameter.get('provider_id', None)
    ec_uuid = parameter.get('ec_uuid', None)

    if provider_id:
        branding_info = enterprise_utils.get_enterprise_branding_info_by_provider_id(identity_provider_id=provider_id)
    elif ec_uuid:
        branding_info = enterprise_utils.get_enterprise_branding_info_by_ec_uuid(ec_uuid=ec_uuid)

    logo_url = None
    if branding_info and branding_info.logo:
        logo_url = branding_info.logo.url

    return logo_url


def set_enterprise_branding_filter_param(request, provider_id):
    """
    Setting 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' in session. 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS'
    either be provider_id or ec_uuid. e.g. {provider_id: 'xyz'} or {ec_src: enterprise_customer_uuid}
    """
    ec_uuid = request.GET.get('ec_src', None)
    if provider_id:
        LOGGER.info(
            "Session key 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' has been set with provider_id '%s'",
            provider_id
        )
        request.session[ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS] = {'provider_id': provider_id}

    elif ec_uuid:
        # we are assuming that none sso based enterprise will return Enterprise Customer uuid as 'ec_src' in query
        # param e.g. edx.org/foo/bar?ec_src=6185ed46-68a4-45d6-8367-96c0bf70d1a6
        LOGGER.info(
            "Session key 'ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS' has been set with ec_uuid '%s'", ec_uuid
        )
        request.session[ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS] = {'ec_uuid': ec_uuid}


def get_enterprise_branding_filter_param(request):
    """
    :return Filter parameter from session for enterprise customer branding information.

    """
    return request.session.get(ENTERPRISE_CUSTOMER_BRANDING_OVERRIDE_DETAILS, None)


def get_cache_key(**kwargs):
    """
    Get MD5 encoded cache key for given arguments.

    Here is the format of key before MD5 encryption.
        key1:value1__key2:value2 ...

    Example:
        >>> get_cache_key(site_domain="example.com", resource="enterprise-learner")
        # Here is key format for above call
        # "site_domain:example.com__resource:enterprise-learner"
        a54349175618ff1659dee0978e3149ca

    Arguments:
        **kwargs: Key word arguments that need to be present in cache key.

    Returns:
         An MD5 encoded key uniquely identified by the key word arguments.
    """
    key = '__'.join(['{}:{}'.format(item, value) for item, value in six.iteritems(kwargs)])

    return hashlib.md5(key).hexdigest()


def get_enterprise_learner_data(site, user):
    """
    Client API operation adapter/wrapper
    """
    if not enterprise_enabled():
        return None

    enterprise_learner_data = EnterpriseApiClient().fetch_enterprise_learner_data(site=site, user=user)
    if enterprise_learner_data:
        return enterprise_learner_data['results']


def get_dashboard_consent_notification(request, user, course_enrollments):
    """
    If relevant to the request at hand, create a banner on the dashboard indicating consent failed.

    Args:
        request: The WSGIRequest object produced by the user browsing to the Dashboard page.
        user: The logged-in user
        course_enrollments: A list of the courses to be rendered on the Dashboard page.

    Returns:
        str: Either an empty string, or a string containing the HTML code for the notification banner.
    """
    enrollment = None
    enterprise_enrollment = None
    course_id = request.GET.get(CONSENT_FAILED_PARAMETER)

    if course_id:
        for course_enrollment in course_enrollments:
            if str(course_enrollment.course_id) == course_id:
                enrollment = course_enrollment
                break

        try:
            enterprise_enrollment = EnterpriseCourseEnrollment.objects.get(
                course_id=course_id,
                enterprise_customer_user__user_id=user.id,
            )
        except EnterpriseCourseEnrollment.DoesNotExist:
            pass

    if enterprise_enrollment and enrollment:
        enterprise_customer = enterprise_enrollment.enterprise_customer_user.enterprise_customer
        contact_info = getattr(enterprise_customer, 'contact_email', None)

        if contact_info is None:
            message_template = _(
                'If you have concerns about sharing your data, please contact your administrator '
                'at {enterprise_customer_name}.'
            )
        else:
            message_template = _(
                'If you have concerns about sharing your data, please contact your administrator '
                'at {enterprise_customer_name} at {contact_info}.'
            )

        message = message_template.format(
            enterprise_customer_name=enterprise_customer.name,
            contact_info=contact_info,
        )
        title = _(
            'Enrollment in {course_name} was not complete.'
        ).format(
            course_name=enrollment.course_overview.display_name,
        )

        return render_to_string(
            'enterprise_support/enterprise_consent_declined_notification.html',
            {
                'title': title,
                'message': message,
            }
        )
    return ''


def is_course_in_enterprise_catalog(site, course_id, user, enterprise_catalog_id):
    """
    Verify that the provided course id exists in the site base list of course
    run keys from the provided enterprise course catalog.

    Arguments:
        course_id (str): The course ID.
        site: (django.contrib.sites.Site) site instance
        enterprise_catalog_id (Int): Course catalog id of enterprise

    Returns:
        Boolean

    """
    cache_key = get_cache_key(
        site_domain=site.domain,
        resource='catalogs.contains',
        course_id=course_id,
        catalog_id=enterprise_catalog_id
    )
    response = cache.get(cache_key)
    if not response:
        try:
            # GET: /api/v1/catalogs/{catalog_id}/contains?course_run_id={course_run_ids}
            response = course_discovery_api_client(user=user).catalogs(enterprise_catalog_id).contains.get(
                course_run_id=course_id
            )
            cache.set(cache_key, response, settings.COURSES_API_CACHE_TIMEOUT)
        except (ConnectionError, SlumberBaseException, Timeout):
            LOGGER.exception('Unable to connect to Course Catalog service for catalog contains endpoint.')
            return False

    try:
        return response['courses'][course_id]
    except KeyError:
        return False
