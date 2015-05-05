""" Commerce app. """
from django.conf import settings
from ecommerce_api_client.client import EcommerceApiClient


def ecommerce_api_client(user):
    """ Returns an E-Commerce API client setup with authentication for the specified user. """
    return EcommerceApiClient(settings.ECOMMERCE_API_URL, settings.ECOMMERCE_API_SIGNING_KEY, user.username,
                              user.email)
