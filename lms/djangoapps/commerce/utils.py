"""Utilities to assist with commerce tasks."""
from urllib import urlencode
from urlparse import urljoin

import waffle
from django.conf import settings

from commerce.models import CommerceConfiguration
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def is_account_activation_requirement_disabled():
    """
    Checks to see if the django-waffle switch for disabling the account activation requirement is active

    Returns:
        Boolean value representing switch status
    """
    switch_name = configuration_helpers.get_value(
        'DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH',
        settings.DISABLE_ACCOUNT_ACTIVATION_REQUIREMENT_SWITCH
    )
    return waffle.switch_is_active(switch_name)


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

        return self.get_absolute_ecommerce_url(CommerceConfiguration.DEFAULT_RECEIPT_PAGE_URL + order_number)

    def is_enabled(self, user):
        """
        Determines the availability of the EcommerceService based on user activation and service configuration.
        Note: If the user is anonymous we bypass the user activation gate and only look at the service config.

        Returns:
            Boolean
        """
        user_is_active = user.is_active or is_account_activation_requirement_disabled()
        allow_user = user_is_active or user.is_anonymous()
        return allow_user and self.config.checkout_on_ecommerce_service

    def payment_page_url(self):
        """ Return the URL for the checkout page.

        Example:
            http://localhost:8002/basket/single_item/
        """
        return self.get_absolute_ecommerce_url(self.config.single_course_checkout_page)

    def get_checkout_page_url(self, *skus):
        """ Construct the URL to the ecommerce checkout page and include products.

        Args:
            skus (list): List of SKUs associated with products to be added to basket

        Returns:
            Absolute path to the ecommerce checkout page showing basket that contains specified products.

        Example:
            http://localhost:8002/basket/add/?sku=5H3HG5&sku=57FHHD
        """
        return '{checkout_page_path}?{skus}'.format(
            checkout_page_path=self.get_absolute_ecommerce_url(self.config.MULTIPLE_ITEMS_BASKET_PAGE_URL),
            skus=urlencode({'sku': skus}, doseq=True),
        )
