""" Commerce app. """
from django.conf import settings
from ecommerce_api_client.client import EcommerceApiClient
from eventtracking import tracker


def create_tracking_context(user):
    """ Assembles attributes from user and request objects to be sent along
    in ecommerce api calls for tracking purposes. """
    return {
        'lms_user_id': user.id,
        'lms_client_id': tracker.get_tracker().resolve_context().get('client_id')
    }


def is_commerce_service_configured():
    """
    Return a Boolean indicating whether or not configuration is present to use
    the external commerce service.
    """
    return bool(settings.ECOMMERCE_API_URL and settings.ECOMMERCE_API_SIGNING_KEY)


def ecommerce_api_client(user):
    """ Returns an E-Commerce API client setup with authentication for the specified user. """
    return EcommerceApiClient(settings.ECOMMERCE_API_URL, settings.ECOMMERCE_API_SIGNING_KEY, user.username,
                              user.profile.name, user.email, tracking_context=create_tracking_context(user))


# this is here to support registering the signals in signals.py
from commerce import signals  # pylint: disable=unused-import
