""" Commerce API Service. """


import requests
import slumber
from django.conf import settings
from edx_rest_api_client.auth import BearerAuth, JwtAuth, SuppliedJwtAuth
from eventtracking import tracker

from openedx.core.djangoapps.oauth_dispatch.jwt import create_jwt_for_user
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from edx_django_utils.monitoring import set_custom_attribute

REQUEST_CONNECT_TIMEOUT = 3.05
REQUEST_READ_TIMEOUT = 5
ECOMMERCE_DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def create_tracking_context(user):
    """ Assembles attributes from user and request objects to be sent along
    in E-Commerce API calls for tracking purposes. """
    context_tracker = tracker.get_tracker().resolve_context()

    return {
        'lms_user_id': user.id,
        'lms_ip': context_tracker.get('ip'),
    }


def is_commerce_service_configured():
    """
    Return a Boolean indicating whether or not configuration is present to use the external commerce service.
    """
    ecommerce_api_url = configuration_helpers.get_value('ECOMMERCE_API_URL', settings.ECOMMERCE_API_URL)
    return bool(ecommerce_api_url)


def get_ecommerce_api_base_url():
    """
    Returns an E-Commerce API base URL.
    """
    return configuration_helpers.get_value('ECOMMERCE_API_URL', settings.ECOMMERCE_API_URL)


def ecommerce_api_client(user, session=None):
    """
    Returns an E-Commerce API client setup with authentication for the specified user.

    DEPRECATED: To be replaced with get_ecommerce_api_client.
    """
    claims = {'tracking_context': create_tracking_context(user)}
    scopes = [
        'user_id',
        'email',
        'profile'
    ]
    jwt = create_jwt_for_user(user, additional_claims=claims, scopes=scopes)

    return DeprecatedRestApiClient(
        configuration_helpers.get_value('ECOMMERCE_API_URL', settings.ECOMMERCE_API_URL),
        jwt=jwt,
        session=session
    )


def get_ecommerce_api_client(user):
    """
    Returns an E-Commerce API client setup with authentication for the specified user.
    """
    claims = {'tracking_context': create_tracking_context(user)}
    scopes = [
        'user_id',
        'email',
        'profile'
    ]
    jwt = create_jwt_for_user(user, additional_claims=claims, scopes=scopes)

    client = requests.Session()
    client.auth = SuppliedJwtAuth(jwt)

    return client


class DeprecatedRestApiClient(slumber.API):
    """
    API client for edX REST API.

    (deprecated)  See docs/decisions/0002-oauth-api-client-replacement.rst.
    """

    @classmethod
    def user_agent(cls):
        return USER_AGENT

    @classmethod
    def get_oauth_access_token(cls, url, client_id, client_secret, token_type='bearer',
                               timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT)):
        #     'To help transition to OAuthAPIClient, use DeprecatedRestApiClient.get_and_cache_jwt_oauth_access_token instead'
        #     'of DeprecatedRestApiClient.get_oauth_access_token to share cached jwt token used by OAuthAPIClient.'
        return get_oauth_access_token(url, client_id, client_secret, token_type=token_type, timeout=timeout)

    @classmethod
    def get_and_cache_jwt_oauth_access_token(cls, url, client_id, client_secret,
                                             timeout=(REQUEST_CONNECT_TIMEOUT, REQUEST_READ_TIMEOUT)):
        return get_and_cache_oauth_access_token(url, client_id, client_secret, token_type="jwt", timeout=timeout)

    def __init__(self, url, signing_key=None, username=None, full_name=None, email=None,
                 timeout=5, issuer=None, expires_in=30, tracking_context=None, oauth_access_token=None,
                 session=None, jwt=None, **kwargs):
        """
        DeprecatedRestApiClient is deprecated. Use OAuthAPIClient instead.

        Instantiate a new client. You can pass extra kwargs to Slumber like
        'append_slash'.

        Raises:
            ValueError: If a URL is not provided.

        """
        set_custom_attribute('api_client', 'DeprecatedRestApiClient')
        if not url:
            raise ValueError('An API url must be supplied!')

        if jwt:
            auth = SuppliedJwtAuth(jwt)
        elif oauth_access_token:
            auth = BearerAuth(oauth_access_token)
        elif signing_key and username:
            auth = JwtAuth(username, full_name, email, signing_key,
                           issuer=issuer, expires_in=expires_in, tracking_context=tracking_context)
        else:
            auth = None

        session = session or requests.Session()
        session.headers['User-Agent'] = self.user_agent()

        session.timeout = timeout
        super().__init__(
            url,
            session=session,
            auth=auth,
            **kwargs
        )
