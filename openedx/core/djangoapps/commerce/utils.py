""" Commerce API Service. """
from django.conf import settings
from edx_rest_api_client.client import EdxRestApiClient
from eventtracking import tracker

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
    return bool(settings.ECOMMERCE_API_URL and settings.ECOMMERCE_API_SIGNING_KEY)


def ecommerce_api_client(user):
    """ Returns an E-Commerce API client setup with authentication for the specified user. """
    return EdxRestApiClient(settings.ECOMMERCE_API_URL,
                            settings.ECOMMERCE_API_SIGNING_KEY,
                            user.username,
                            user.profile.name,
                            user.email,
                            tracking_context=create_tracking_context(user),
                            issuer=settings.JWT_ISSUER,
                            expires_in=settings.JWT_EXPIRATION)
