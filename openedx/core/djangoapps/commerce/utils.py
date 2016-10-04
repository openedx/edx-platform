""" Commerce API Service. """
from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient
from eventtracking import tracker

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

ECOMMERCE_DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def create_tracking_context(user):
    """ Assembles attributes from user and request objects to be sent along
    in ecommerce api calls for tracking purposes. """
    context_tracker = tracker.get_tracker().resolve_context()

    return {
        'lms_user_id': user.id,
        'lms_client_id': context_tracker.get('client_id'),
        'lms_ip': context_tracker.get('ip'),
    }


def is_commerce_service_configured():
    """
    Return a Boolean indicating whether or not configuration is present to use
    the external commerce service.
    """
    ecommerce_api_url = configuration_helpers.get_value("ECOMMERCE_API_URL", settings.ECOMMERCE_API_URL)
    ecommerce_api_signing_key = configuration_helpers.get_value(
        "ECOMMERCE_API_SIGNING_KEY", settings.ECOMMERCE_API_SIGNING_KEY,
    )
    return bool(ecommerce_api_url and ecommerce_api_signing_key)


def ecommerce_api_client(user, session=None):
    """ Returns an E-Commerce API client setup with authentication for the specified user. """
    jwt_auth = configuration_helpers.get_value("JWT_AUTH", settings.JWT_AUTH)
    return EdxRestApiClient(
        configuration_helpers.get_value("ECOMMERCE_API_URL", settings.ECOMMERCE_API_URL),
        configuration_helpers.get_value("ECOMMERCE_API_SIGNING_KEY", settings.ECOMMERCE_API_SIGNING_KEY),
        user.username,
        user.profile.name if hasattr(user, 'profile') else None,
        user.email,
        tracking_context=create_tracking_context(user),
        issuer=jwt_auth['JWT_ISSUER'],
        expires_in=jwt_auth['JWT_EXPIRATION'],
        session=session
    )
