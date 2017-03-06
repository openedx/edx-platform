"""Utilities to assist with commerce tasks."""
import logging
from urlparse import urljoin

from django.conf import settings

from commerce.models import CommerceConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

log = logging.getLogger(__name__)


def audit_log(name, **kwargs):
    """DRY helper used to emit an INFO-level log message.

    Messages logged with this function are used to construct an audit trail. Log messages
    should be emitted immediately after the event they correspond to has occurred and, if
    applicable, after the database has been updated. These log messages use a verbose
    key-value pair syntax to make it easier to extract fields when parsing the application's
    logs.

    This function is variadic, accepting a variable number of keyword arguments.

    Arguments:
        name (str): The name of the message to log. For example, 'payment_received'.

    Keyword Arguments:
        Indefinite. Keyword arguments are strung together as comma-separated key-value
        pairs ordered alphabetically by key in the resulting log message.

    Returns:
        None
    """
    # Joins sorted keyword argument keys and values with an "=", wraps each value
    # in quotes, and separates each pair with a comma and a space.
    payload = u', '.join(['{k}="{v}"'.format(k=k, v=v) for k, v in sorted(kwargs.items())])
    message = u'{name}: {payload}'.format(name=name, payload=payload)

    log.info(message)


class EcommerceService(object):
    """ Helper class for ecommerce service integration. """
    def __init__(self):
        self.config = CommerceConfiguration.current()

    def is_enabled(self, user):
        """
        Determines the availability of the EcommerceService based on user activation and service configuration.
        Note: If the user is anonymous we bypass the user activation gate and only look at the service config.

        Returns:
            Boolean
        """
        allow_user = user.is_active or user.is_anonymous()
        return allow_user and self.config.checkout_on_ecommerce_service

    def payment_page_url(self):
        """ Return the URL for the checkout page.

        Example:
            http://localhost:8002/basket/single_item/
        """
        ecommerce_url_root = configuration_helpers.get_value(
            'ECOMMERCE_PUBLIC_URL_ROOT',
            settings.ECOMMERCE_PUBLIC_URL_ROOT,
        )
        return urljoin(ecommerce_url_root, self.config.single_course_checkout_page)

    def checkout_page_url(self, sku):
        """ Construct the URL to the ecommerce checkout page and include a product.

        Example:
            http://localhost:8002/basket/single_item/?sku=5H3HG5
        """
        return "{}?sku={}".format(self.payment_page_url(), sku)
