"""
Helpers to access the enterprise app
"""
import logging

from functools import wraps
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.utils.http import urlencode
from edx_rest_api_client.client import EdxRestApiClient
try:
    from enterprise import utils as enterprise_utils
    from enterprise.utils import consent_necessary_for_course
except ImportError:
    pass
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.lib.token_utils import JwtBuilder
from slumber.exceptions import HttpClientError, HttpServerError


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
        'next': request.build_absolute_uri(return_path)
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
