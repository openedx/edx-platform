"""Utilities to assist with commerce tasks."""
from urlparse import urljoin

from django.conf import settings

from commerce.models import CommerceConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


class EcommerceService(object):
    """ Helper class for ecommerce service integration. """
    def __init__(self):
        self.config = CommerceConfiguration.current()

    @property
    def ecommerce_url_root(self):
        """ Retrieve Ecommerce service public url root. """
        return configuration_helpers.get_value('ECOMMERCE_PUBLIC_URL_ROOT', settings.ECOMMERCE_PUBLIC_URL_ROOT)

    def get_absolute_ecommerce_url(self, ecommerce_page_url):
        """ Return the absolute URL to the ecommerce page.

        Args:
            ecommerce_page_url (str): Relative path to the ecommerce page.

        Returns:
            Absolute path to the ecommerce page.
        """
        return urljoin(self.ecommerce_url_root, ecommerce_page_url)

    def get_receipt_page_url(self, order_number):
        """
        Gets the URL for the Order Receipt page hosted by the ecommerce service.

        Args:
            order_number (str): Order number.

        Returns:
            Receipt page for the specified Order.
        """
        ecommerce_receipt_page_url = configuration_helpers.get_value('ECOMMERCE_RECEIPT_PAGE_URL')
        if ecommerce_receipt_page_url:
            receipt_page_url = self.get_absolute_ecommerce_url(ecommerce_receipt_page_url)
        else:
            receipt_page_url = self.config.receipt_page
        return receipt_page_url + order_number

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
        return self.get_absolute_ecommerce_url(self.config.single_course_checkout_page)

    def checkout_page_url(self, sku):
        """ Construct the URL to the ecommerce checkout page and include a product.

        Example:
            http://localhost:8002/basket/single_item/?sku=5H3HG5
        """
        return "{}?sku={}".format(self.get_absolute_ecommerce_url(self.config.single_course_checkout_page), sku)
