"""
APIs providing support for enterprise functionality.
"""


import logging
import traceback
from functools import wraps

from crum import get_current_request
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.http import urlencode
from django.utils.translation import ugettext as _
from edx_django_utils.cache import TieredCache, get_cache_key
from edx_rest_api_client.client import EdxRestApiClient
from slumber.exceptions import HttpClientError, HttpNotFoundError, HttpServerError

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from openedx.core.djangolib.markup import HTML, Text
from openedx.features.enterprise_support.utils import get_data_consent_share_cache_key
from common.djangoapps.third_party_auth.pipeline import get as get_partial_pipeline
from common.djangoapps.third_party_auth.provider import Registry

try:
    from enterprise.models import (
        EnterpriseCustomer,
        EnterpriseCustomerIdentityProvider,
        EnterpriseCustomerUser,
        PendingEnterpriseCustomerUser
    )
    from enterprise.api.v1.serializers import EnterpriseCustomerUserReadOnlySerializer
    from consent.models import DataSharingConsent, DataSharingConsentTextOverrides
except ImportError:  # pragma: no cover
    pass


CONSENT_FAILED_PARAMETER = 'consent_failed'
LOGGER = logging.getLogger("edx.enterprise_helpers")
ENTERPRISE_CUSTOMER_KEY_NAME = 'enterprise_customer'

# See https://open-edx-proposals.readthedocs.io/en/latest/oep-0022-bp-django-caches.html#common-caching-defect-and-fix
_CACHE_MISS = '__CACHE_MISS__'


class EnterpriseApiException(Exception):
    """
    Exception for errors while communicating with the Enterprise service API.
    """


class ConsentApiClient(object):
    """
    Class for producing an Enterprise Consent service API client
    """

    def __init__(self, user):
        """
        Initialize an authenticated Consent service API client by using the
        provided user.
        """
        jwt = create_jwt_for_user(user)
        url = configuration_helpers.get_value('ENTERPRISE_CONSENT_API_URL', settings.ENTERPRISE_CONSENT_API_URL)
        self.client = EdxRestApiClient(
            url,
            jwt=jwt,
            append_slash=False,
        )
        self.consent_endpoint = self.client.data_sharing_consent

    def revoke_consent(self, **kwargs):
        """
        Revoke consent from any existing records that have it at the given scope.

        This endpoint takes any given kwargs, which are understood as filtering the
        conceptual scope of the consent involved in the request.
        """
        return self.consent_endpoint.delete(**kwargs)

    def provide_consent(self, **kwargs):
        """
        Provide consent at the given scope.

        This endpoint takes any given kwargs, which are understood as filtering the
        conceptual scope of the consent involved in the request.
        """
        return self.consent_endpoint.post(kwargs)

    def consent_required(self, enrollment_exists=False, **kwargs):
        """
        Determine if consent is required at the given scope.

        This endpoint takes any given kwargs, which are understood as filtering the
        conceptual scope of the consent involved in the request.
        """

        # Call the endpoint with the given kwargs, and check the value that it provides.
        response = self.consent_endpoint.get(**kwargs)

        LOGGER.info(
            '[ENTERPRISE DSC] Consent Requirement Info. APIParams: [%s], APIResponse: [%s], EnrollmentExists: [%s]',
            kwargs,
            response,
            enrollment_exists,
        )

        # No Enterprise record exists, but we're already enrolled in a course. So, go ahead and proceed.
        if enrollment_exists and not response.get('exists', False):
            return False

        # In all other cases, just trust the Consent API.
        return response['consent_required']


class EnterpriseServiceClientMixin(object):
    """
    Class for initializing an Enterprise API clients with service user.
    """

    def __init__(self):
        """
        Initialize an authenticated Enterprise API client by using the
        Enterprise worker user by default.
        """
        user = User.objects.get(username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME)
        super(EnterpriseServiceClientMixin, self).__init__(user)


class ConsentApiServiceClient(EnterpriseServiceClientMixin, ConsentApiClient):
    """
    Class for producing an Enterprise Consent API client with service user.
    """


class EnterpriseApiClient(object):
    """
    Class for producing an Enterprise service API client.
    """

    def __init__(self, user):
        """
        Initialize an authenticated Enterprise service API client by using the
        provided user.
        """
        self.user = user
        jwt = create_jwt_for_user(user)
        self.client = EdxRestApiClient(
            configuration_helpers.get_value('ENTERPRISE_API_URL', settings.ENTERPRISE_API_URL),
            jwt=jwt
        )

    def get_enterprise_customer(self, uuid):
        endpoint = getattr(self.client, 'enterprise-customer')
        return endpoint(uuid).get()

    def post_enterprise_course_enrollment(self, username, course_id, consent_granted):
        """
        Create an EnterpriseCourseEnrollment by using the corresponding serializer (for validation).
        """
        data = {
            'username': username,
            'course_id': course_id,
            'consent_granted': consent_granted,
        }
        endpoint = getattr(self.client, 'enterprise-course-enrollment')
        try:
            endpoint.post(data=data)
        except (HttpClientError, HttpServerError):
            message = (
                u"An error occured while posting EnterpriseCourseEnrollment for user {username} and "
                u"course run {course_id} (consent_granted value: {consent_granted})"
            ).format(
                username=username,
                course_id=course_id,
                consent_granted=consent_granted,
            )
            LOGGER.exception(message)
            raise EnterpriseApiException(message)

    def fetch_enterprise_learner_data(self, user):
        """
        Fetch information related to enterprise from the Enterprise Service.

        Example:
            fetch_enterprise_learner_data(user)

        Argument:
            user: (User) django auth user

        Returns:
            dict:
            {
                "count": 1,
                "num_pages": 1,
                "current_page": 1,
                "next": null,
                "start": 0,
                "previous": null
                "results": [
                    {
                        "enterprise_customer": {
                            "uuid": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                            "name": "TestShib",
                            "active": true,
                            "site": {
                                "domain": "example.com",
                                "name": "example.com"
                            },
                            "enable_data_sharing_consent": true,
                            "enforce_data_sharing_consent": "at_login",
                            "branding_configuration": {
                                "enterprise_customer": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                "logo": "https://open.edx.org/sites/all/themes/edx_open/logo.png"
                            },
                            "enterprise_customer_entitlements": [
                                {
                                    "enterprise_customer": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                    "entitlement_id": 69
                                }
                            ],
                            "replace_sensitive_sso_username": False,
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
                        "data_sharing_consent_records": [
                            {
                                "username": "staff",
                                "enterprise_customer_uuid": "cf246b88-d5f6-4908-a522-fc307e0b0c59",
                                "exists": true,
                                "course_id": "course-v1:edX DemoX Demo_Course",
                                "consent_provided": true,
                                "consent_required": false
                            }
                        ]
                    }
                ],
            }

        Raises:
            ConnectionError: requests exception "ConnectionError", raised if if ecommerce is unable to connect
                to enterprise api server.
            SlumberBaseException: base slumber exception "SlumberBaseException", raised if API response contains
                http error status like 4xx, 5xx etc.
            Timeout: requests exception "Timeout", raised if enterprise API is taking too long for returning
                a response. This exception is raised for both connection timeout and read timeout.

        """
        if not user.is_authenticated:
            return None

        api_resource_name = 'enterprise-learner'

        try:
            endpoint = getattr(self.client, api_resource_name)
            querystring = {'username': user.username}
            response = endpoint().get(**querystring)
        except (HttpClientError, HttpServerError):
            LOGGER.exception(
                u'Failed to get enterprise-learner for user [%s] with client user [%s]. Caller: %s, Request PATH: %s',
                user.username,
                self.user.username,
                "".join(traceback.format_stack()),
                get_current_request().META['PATH_INFO'],
            )
            return None

        return response


class EnterpriseApiServiceClient(EnterpriseServiceClientMixin, EnterpriseApiClient):
    """
    Class for producing an Enterprise service API client with service user.
    """

    def get_enterprise_customer(self, uuid):
        """
        Fetch enterprise customer with enterprise service user and cache the
        API response`.
        """
        enterprise_customer = enterprise_customer_from_cache(uuid=uuid)
        if enterprise_customer is _CACHE_MISS:
            endpoint = getattr(self.client, 'enterprise-customer')
            enterprise_customer = endpoint(uuid).get()
            if enterprise_customer:
                cache_enterprise(enterprise_customer)

        return enterprise_customer


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
        consent_url = get_enterprise_consent_url(request, course_id, enrollment_exists=True)
        if consent_url:
            real_user = getattr(request.user, 'real_user', request.user)
            LOGGER.info(
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
    return 'enterprise' in settings.INSTALLED_APPS and settings.FEATURES.get('ENABLE_ENTERPRISE_INTEGRATION', False)


def enterprise_is_enabled(otherwise=None):
    """Decorator which requires that the Enterprise feature be enabled before the function can run."""
    def decorator(func):
        """Decorator for ensuring the Enterprise feature is enabled."""
        def wrapper(*args, **kwargs):
            if enterprise_enabled():
                return func(*args, **kwargs)
            return otherwise
        return wrapper
    return decorator


def get_enterprise_customer_cache_key(uuid, username=settings.ENTERPRISE_SERVICE_WORKER_USERNAME):
    """The cache key used to get cached Enterprise Customer data."""
    return get_cache_key(
        resource='enterprise-customer',
        resource_id=uuid,
        username=username,
    )


def cache_enterprise(enterprise_customer):
    """Add this customer's data to the Django cache."""
    cache_key = get_enterprise_customer_cache_key(enterprise_customer['uuid'])
    cache.set(cache_key, enterprise_customer, settings.ENTERPRISE_API_CACHE_TIMEOUT)


def enterprise_customer_from_cache(uuid):
    """
    Retrieve enterprise customer data associated with the given ``uuid`` from the Django cache,
    returning a ``__CACHE_MISS__`` if absent.
    """
    cache_key = get_enterprise_customer_cache_key(uuid)
    return cache.get(cache_key, _CACHE_MISS)


def add_enterprise_customer_to_session(request, enterprise_customer):
    """ Add the given enterprise_customer data to the request's session if user is authenticated. """
    if request.user.is_authenticated:
        request.session[ENTERPRISE_CUSTOMER_KEY_NAME] = enterprise_customer


def enterprise_customer_from_session(request):
    """
    Retrieve enterprise_customer data from the request's session,
    returning a ``__CACHE_MISS__`` if absent.
    """
    return request.session.get(ENTERPRISE_CUSTOMER_KEY_NAME, _CACHE_MISS)


def enterprise_customer_uuid_from_session(request):
    """
    Retrieve an enterprise customer UUID from the request's session,
    returning a ``__CACHE_MISS__`` if absent.  Note that this may
    return ``None``, which indicates that we've previously looked
    for an associated customer for this request's user, and
    none was present.
    """
    customer_data = enterprise_customer_from_session(request)
    if customer_data is not _CACHE_MISS:
        customer_data = customer_data or {}
        return customer_data.get('uuid')
    return _CACHE_MISS


def enterprise_customer_uuid_from_query_param(request):
    """
    Returns an enterprise customer UUID from the given request's GET data,
    or ``__CACHE_MISS__`` if not present.
    """
    return request.GET.get(ENTERPRISE_CUSTOMER_KEY_NAME, _CACHE_MISS)


def enterprise_customer_uuid_from_cookie(request):
    """
    Returns an enterprise customer UUID from the given request's cookies,
    or ``__CACHE_MISS__`` if not present.
    """
    return request.COOKIES.get(settings.ENTERPRISE_CUSTOMER_COOKIE_NAME, _CACHE_MISS)


@enterprise_is_enabled()
def enterprise_customer_from_api(request):
    """Use an API to get Enterprise Customer data from request context clues."""
    enterprise_customer = None
    enterprise_customer_uuid = enterprise_customer_uuid_for_request(request)
    if enterprise_customer_uuid is _CACHE_MISS:
        # enterprise_customer_uuid_for_request() `shouldn't` return a __CACHE_MISS__,
        # but just in case it does, we check for it and return early if found.
        return enterprise_customer

    if enterprise_customer_uuid:
        # If we were able to obtain an EnterpriseCustomer UUID, go ahead
        # and use it to attempt to retrieve EnterpriseCustomer details
        # from the EnterpriseCustomer API.
        enterprise_api_client = (
            EnterpriseApiClient(user=request.user)
            if request.user.is_authenticated
            else EnterpriseApiServiceClient()
        )

        try:
            enterprise_customer = enterprise_api_client.get_enterprise_customer(enterprise_customer_uuid)
        except HttpNotFoundError:
            enterprise_customer = None
    return enterprise_customer


@enterprise_is_enabled()
def enterprise_customer_uuid_for_request(request):
    """
    Check all the context clues of the request to gather a particular EnterpriseCustomer's UUID.
    """
    sso_provider_id = request.GET.get('tpa_hint')
    running_pipeline = get_partial_pipeline(request)
    if running_pipeline:
        # Determine if the user is in the middle of a third-party auth pipeline,
        # and set the sso_provider_id parameter to match if so.
        sso_provider_id = Registry.get_from_pipeline(running_pipeline).provider_id

    if sso_provider_id:
        # If we have a third-party auth provider, get the linked enterprise customer.
        try:
            # FIXME: Implement an Enterprise API endpoint where we can get the EC
            # directly via the linked SSO provider
            # Check if there's an Enterprise Customer such that the linked SSO provider
            # has an ID equal to the ID we got from the running pipeline or from the
            # request tpa_hint URL parameter.
            enterprise_customer_uuid = EnterpriseCustomer.objects.get(
                enterprise_customer_identity_provider__provider_id=sso_provider_id
            ).uuid
        except EnterpriseCustomer.DoesNotExist:
            LOGGER.info(
                '[ENTERPRISE DSC] Customer not found using SSO Provider ID. User: [%s], SSOProviderID: [%s]',
                request.user.username,
                sso_provider_id
            )
            enterprise_customer_uuid = None
    else:
        enterprise_customer_uuid = _customer_uuid_from_query_param_cookies_or_session(request)

    if enterprise_customer_uuid is _CACHE_MISS or enterprise_customer_uuid is None:
        if not request.user.is_authenticated:
            return None

        # If there's no way to get an Enterprise UUID for the request, check to see
        # if there's already an Enterprise attached to the requesting user on the backend.
        enterprise_customer = None
        learner_data = get_enterprise_learner_data_from_db(request.user)
        if learner_data:
            enterprise_customer = learner_data[0]['enterprise_customer']
            enterprise_customer_uuid = enterprise_customer['uuid']
            cache_enterprise(enterprise_customer)
        else:
            enterprise_customer_uuid = None

        # Now that we've asked the database for this users's enterprise customer data,
        # add it to their session (even if it's null/empty, which indicates the user
        # has no associated enterprise customer).
        LOGGER.info(
            '[ENTERPRISE DSC] Updating Session. User: [%s], UserAuthenticated: [%s], EnterpriseCustomer: [%s]',
            request.user.username,
            request.user.is_authenticated,
            enterprise_customer
        )
        add_enterprise_customer_to_session(request, enterprise_customer)

    return enterprise_customer_uuid


def _customer_uuid_from_query_param_cookies_or_session(request):
    """
    Helper function that plucks a customer UUID out of the given requests's
    query params, cookie, or session data.
    Returns ``__CACHE_MISS__`` if none of those keys are present in the request.
    """
    for function in (
        enterprise_customer_uuid_from_query_param,
        enterprise_customer_uuid_from_cookie,
        enterprise_customer_uuid_from_session,
    ):
        enterprise_customer_uuid = function(request)
        if enterprise_customer_uuid is not _CACHE_MISS:
            LOGGER.info(
                '[ENTERPRISE DSC] Customer Info. User: [%s], Function: [%s], UUID: [%s]',
                request.user.username,
                function,
                enterprise_customer_uuid
            )
            return enterprise_customer_uuid

    return _CACHE_MISS


@enterprise_is_enabled()
def enterprise_customer_for_request(request):
    """
    Check all the context clues of the request to determine if
    the request being made is tied to a particular EnterpriseCustomer.
    """
    enterprise_customer = enterprise_customer_from_session(request)
    if enterprise_customer is _CACHE_MISS:
        enterprise_customer = enterprise_customer_from_api(request)
        LOGGER.info(
            '[ENTERPRISE DSC] Updating Session. User: [%s], UserAuthenticated: [%s], EnterpriseCustomer: [%s]',
            request.user.username,
            request.user.is_authenticated,
            enterprise_customer
        )
        add_enterprise_customer_to_session(request, enterprise_customer)
    return enterprise_customer


@enterprise_is_enabled(otherwise=False)
def consent_needed_for_course(request, user, course_id, enrollment_exists=False):
    """
    Wrap the enterprise app check to determine if the user needs to grant
    data sharing permissions before accessing a course.
    """
    LOGGER.info(
        u"Determining if user [{username}] must consent to data sharing for course [{course_id}]".format(
            username=user.username,
            course_id=course_id
        )
    )

    consent_cache_key = get_data_consent_share_cache_key(user.id, course_id)
    data_sharing_consent_needed_cache = TieredCache.get_cached_response(consent_cache_key)
    if data_sharing_consent_needed_cache.is_found and data_sharing_consent_needed_cache.value == 0:
        LOGGER.info(
            u"Consent from user [{username}] is not needed for course [{course_id}]. The DSC cache was checked,"
            u" and the value was 0.".format(
                username=user.username,
                course_id=course_id
            )
        )
        return False

    consent_needed = False
    enterprise_learner_details = get_enterprise_learner_data_from_db(user)
    if not enterprise_learner_details:
        LOGGER.info(
            u"Consent from user [{username}] is not needed for course [{course_id}]. The user is not linked to an"
            u" enterprise.".format(
                username=user.username,
                course_id=course_id
            )
        )
    else:
        client = ConsentApiClient(user=request.user)
        current_enterprise_uuid = enterprise_customer_uuid_for_request(request)
        consent_needed = any(
            str(current_enterprise_uuid) == str(learner['enterprise_customer']['uuid'])
            and Site.objects.get(domain=learner['enterprise_customer']['site']['domain']) == request.site
            and client.consent_required(
                username=user.username,
                course_id=course_id,
                enterprise_customer_uuid=current_enterprise_uuid,
                enrollment_exists=enrollment_exists,
            )
            for learner in enterprise_learner_details
        )

        if not consent_needed:
            # TODO: https://openedx.atlassian.net/browse/ENT-3724
            # this whole code branch seems to do nothing other than log some misleading info:
            # the consent requirement doesn't actually fail.  If there's an enterprise or site mismatch,
            # we'll still end up in the else branch of "if consent_needed:" below, where
            # we'll log that consent is not needed, and ultimately, return False.
            # Are we supposed to raise some exceptions in here?
            enterprises = [str(learner['enterprise_customer']['uuid']) for learner in enterprise_learner_details]

            if str(current_enterprise_uuid) not in enterprises:
                LOGGER.info(  # pragma: no cover
                    '[ENTERPRISE DSC] Enterprise mismatch. USER: [%s], CurrentEnterprise: [%s], UserEnterprises: [%s]',
                    user.username,
                    current_enterprise_uuid,
                    enterprises
                )
            else:
                domains = [learner['enterprise_customer']['site']['domain'] for learner in enterprise_learner_details]
                if not Site.objects.filter(domain__in=domains).filter(id=request.site.id).exists():
                    LOGGER.info(  # pragma: no cover
                        '[ENTERPRISE DSC] Site mismatch. USER: [%s], RequestSite: [%s], LearnerEnterpriseDomains: [%s]',
                        user.username,
                        request.site,
                        domains
                    )

        if consent_needed:
            LOGGER.info(
                u"Consent from user [{username}] is needed for course [{course_id}]. The user's current enterprise"
                u" required data sharing consent, and it has not been given.".format(
                    username=user.username,
                    course_id=course_id
                )
            )
        else:
            LOGGER.info(
                u"Consent from user [{username}] is not needed for course [{course_id}]. The user's current enterprise "
                u"does not require data sharing consent.".format(
                    username=user.username,
                    course_id=course_id
                )
            )

    if not consent_needed:
        # Set an ephemeral item in the cache to prevent us from needing
        # to make a Consent API request every time this function is called.
        TieredCache.set_all_tiers(consent_cache_key, 0, settings.DATA_CONSENT_SHARE_CACHE_TIMEOUT)

    return consent_needed


@enterprise_is_enabled(otherwise=set())
def get_consent_required_courses(user, course_ids):
    """
    Returns a set of course_ids that require consent
    Note that this function makes use of the Enterprise models directly instead of using the API calls
    """
    result = set()
    enterprise_learner = EnterpriseCustomerUser.objects.filter(user_id=user.id).first()
    if not enterprise_learner or not enterprise_learner.enterprise_customer:
        return result

    enterprise_uuid = enterprise_learner.enterprise_customer.uuid
    data_sharing_consent = DataSharingConsent.objects.filter(username=user.username,
                                                             course_id__in=course_ids,
                                                             enterprise_customer__uuid=enterprise_uuid)

    for consent in data_sharing_consent:
        if consent.consent_required():
            result.add(consent.course_id)

    return result


@enterprise_is_enabled(otherwise='')
def get_enterprise_consent_url(request, course_id, user=None, return_to=None, enrollment_exists=False):
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
    user = user or request.user

    LOGGER.info(
        u'Getting enterprise consent url for user [{username}] and course [{course_id}].'.format(
            username=user.username,
            course_id=course_id
        )
    )

    if not consent_needed_for_course(request, user, course_id, enrollment_exists=enrollment_exists):
        return None

    if return_to is None:
        return_path = request.path
    else:
        return_path = reverse(return_to, args=(course_id,))

    url_params = {
        'enterprise_customer_uuid': enterprise_customer_uuid_for_request(request),
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
    LOGGER.info(u'Redirecting to %s to complete data sharing consent', full_url)
    return full_url


@enterprise_is_enabled()
def get_enterprise_learner_data_from_api(user):
    """
    Client API operation adapter/wrapper
    """
    if user.is_authenticated:
        enterprise_learner_data = EnterpriseApiClient(user=user).fetch_enterprise_learner_data(user)
        if enterprise_learner_data:
            return enterprise_learner_data['results']


@enterprise_is_enabled()
def get_enterprise_learner_data_from_db(user):
    """
    Query the database directly and use the same serializer that the api call would use to return the same results.
    """
    if user.is_authenticated:
        queryset = EnterpriseCustomerUser.objects.filter(user_id=user.id)
        serializer = EnterpriseCustomerUserReadOnlySerializer(queryset, many=True)
        return serializer.data


@enterprise_is_enabled()
def get_enterprise_learner_portal_enabled_message(request):
    """
    Returns message to be displayed in dashboard if the user is linked to an Enterprise with the Learner Portal enabled.

    Note: request.session[ENTERPRISE_CUSTOMER_KEY_NAME] will be used in case the user is linked to
        multiple Enterprises. Otherwise, it won't exist and the Enterprise Learner data
        will be used. If that doesn't exist return None.

    Args:
        request: request made to the LMS dashboard
    """
    enterprise_customer = enterprise_customer_from_session(request)
    if enterprise_customer is _CACHE_MISS:
        learner_data = get_enterprise_learner_data_from_db(request.user)
        enterprise_customer = learner_data[0]['enterprise_customer'] if learner_data else None
        # Add to session cache regardless of whether it is null
        LOGGER.info(
            '[ENTERPRISE DSC] Updating Session. User: [%s], UserAuthenticated: [%s], EnterpriseCustomer: [%s]',
            request.user.username,
            request.user.is_authenticated,
            enterprise_customer
        )
        add_enterprise_customer_to_session(request, enterprise_customer)
        if enterprise_customer:
            cache_enterprise(enterprise_customer)

    if not enterprise_customer:
        return None

    if enterprise_customer.get('enable_learner_portal', False):
        learner_portal_url = settings.ENTERPRISE_LEARNER_PORTAL_BASE_URL + '/' + enterprise_customer['slug']
        return Text(_(
            "Your organization {bold_start}{enterprise_customer_name}{bold_end} uses a custom dashboard for learning. "
            "{link_start}Click here{link_end} to continue in that experience."
        )).format(
            enterprise_customer_name=enterprise_customer['name'],
            link_start=HTML("<a href='{learner_portal_url}'>").format(
                learner_portal_url=learner_portal_url,
            ),
            link_end=HTML("</a>"),
            bold_start=HTML("<b>"),
            bold_end=HTML("</b>"),
        )
    else:
        return None


def get_consent_notification_data(enterprise_customer):
    """
    Returns the consent notification data from DataSharingConsentPage modal
    """
    title_template = None
    message_template = None
    try:
        consent_page = DataSharingConsentTextOverrides.objects.get(enterprise_customer_id=enterprise_customer['uuid'])
        title_template = consent_page.declined_notification_title
        message_template = consent_page.declined_notification_message
    except DataSharingConsentTextOverrides.DoesNotExist:
        LOGGER.info(
            u"DataSharingConsentPage object doesn't exit for {enterprise_customer_name}".format(
                enterprise_customer_name=enterprise_customer['name']
            )
        )
    return title_template, message_template


@enterprise_is_enabled(otherwise='')
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
    consent_needed = False
    course_id = request.GET.get(CONSENT_FAILED_PARAMETER)

    if course_id:

        enterprise_customer = enterprise_customer_for_request(request)
        if not enterprise_customer:
            return ''

        for course_enrollment in course_enrollments:
            if str(course_enrollment.course_id) == course_id:
                enrollment = course_enrollment
                break

        client = ConsentApiClient(user=request.user)
        consent_needed = client.consent_required(
            enterprise_customer_uuid=enterprise_customer['uuid'],
            username=user.username,
            course_id=course_id,
        )

    if consent_needed and enrollment:

        title_template, message_template = get_consent_notification_data(enterprise_customer)
        if not title_template:
            title_template = _(
                u'Enrollment in {course_title} was not complete.'
            )
        if not message_template:
            message_template = _(
                'If you have concerns about sharing your data, please contact your administrator '
                u'at {enterprise_customer_name}.'
            )

        title = title_template.format(
            course_title=enrollment.course_overview.display_name,
        )
        message = message_template.format(
            enterprise_customer_name=enterprise_customer['name'],
        )

        return render_to_string(
            'enterprise_support/enterprise_consent_declined_notification.html',
            {
                'title': title,
                'message': message,
                'course_name': enrollment.course_overview.display_name,
            }
        )
    return ''


@enterprise_is_enabled()
def insert_enterprise_pipeline_elements(pipeline):
    """
    If the enterprise app is enabled, insert additional elements into the
    pipeline related to enterprise.
    """
    additional_elements = (
        'enterprise.tpa_pipeline.handle_enterprise_logistration',
    )

    insert_point = pipeline.index('social_core.pipeline.social_auth.load_extra_data')
    for index, element in enumerate(additional_elements):
        pipeline.insert(insert_point + index, element)


@enterprise_is_enabled()
def unlink_enterprise_user_from_idp(request, user, idp_backend_name):
    """
    Un-links learner from their enterprise identity provider
    Args:
        request (wsgi request): request object
        user (User): user who initiated disconnect request
        idp_backend_name (str): Name of identity provider's backend

    Returns: None

    """
    enterprise_customer = enterprise_customer_for_request(request)
    if user and enterprise_customer:
        enabled_providers = Registry.get_enabled_by_backend_name(idp_backend_name)
        provider_ids = [enabled_provider.provider_id for enabled_provider in enabled_providers]
        enterprise_customer_idps = EnterpriseCustomerIdentityProvider.objects.filter(
            enterprise_customer__uuid=enterprise_customer['uuid'],
            provider_id__in=provider_ids
        )

        if enterprise_customer_idps:
            try:
                # Unlink user email from each Enterprise Customer.
                for enterprise_customer_idp in enterprise_customer_idps:
                    EnterpriseCustomerUser.objects.unlink_user(
                        enterprise_customer=enterprise_customer_idp.enterprise_customer, user_email=user.email
                    )
            except (EnterpriseCustomerUser.DoesNotExist, PendingEnterpriseCustomerUser.DoesNotExist):
                pass
