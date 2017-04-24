"""Tests of commerce utilities."""
from django.conf import settings
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from mock import patch

from commerce.models import CommerceConfiguration
from commerce.utils import EcommerceService
from openedx.core.lib.log_utils import audit_log
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration
from student.tests.factories import UserFactory

TEST_SITE_CONFIGURATION = {
    'ECOMMERCE_RECEIPT_PAGE_URL': '/checkout/receipt/?order_number='
}


def update_commerce_config(enabled=False, checkout_page='/test_basket/', receipt_page='/checkout/receipt/'):
    """ Enable / Disable CommerceConfiguration model """
    CommerceConfiguration.objects.create(
        checkout_on_ecommerce_service=enabled,
        receipt_page=receipt_page,
        single_course_checkout_page=checkout_page,
    )


class AuditLogTests(TestCase):
    """Tests of the commerce audit logging helper."""
    @patch('openedx.core.lib.log_utils.log')
    def test_log_message(self, mock_log):
        """Verify that log messages are constructed correctly."""
        audit_log('foo', qux='quux', bar='baz')

        # Verify that the logged message contains comma-separated
        # key-value pairs ordered alphabetically by key.
        message = 'foo: bar="baz", qux="quux"'
        self.assertTrue(mock_log.info.called_with(message))


class EcommerceServiceTests(TestCase):
    """Tests for the EcommerceService helper class."""
    SKU = 'TESTSKU'

    def setUp(self):
        self.request_factory = RequestFactory()
        self.user = UserFactory.create()
        self.request = self.request_factory.get("foo")
        update_commerce_config(enabled=True)
        super(EcommerceServiceTests, self).setUp()

    def test_is_enabled(self):
        """Verify that is_enabled() returns True when ecomm checkout is enabled. """
        is_enabled = EcommerceService().is_enabled(self.user)
        self.assertTrue(is_enabled)

        config = CommerceConfiguration.current()
        config.checkout_on_ecommerce_service = False
        config.save()
        is_not_enabled = EcommerceService().is_enabled(self.user)
        self.assertFalse(is_not_enabled)

    @patch('openedx.core.djangoapps.theming.helpers.is_request_in_themed_site')
    def test_is_enabled_for_microsites(self, is_microsite):
        """Verify that is_enabled() returns True if used for a microsite."""
        is_microsite.return_value = True
        is_enabled = EcommerceService().is_enabled(self.user)
        self.assertTrue(is_enabled)

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    def test_ecommerce_url_root(self):
        """Verify that the proper root URL is returned."""
        self.assertEqual(EcommerceService().ecommerce_url_root, 'http://ecommerce_url')

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    def test_get_absolute_ecommerce_url(self):
        """Verify that the proper URL is returned."""
        url = EcommerceService().get_absolute_ecommerce_url('/test_basket/')
        self.assertEqual(url, 'http://ecommerce_url/test_basket/')

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    def test_get_receipt_page_url(self):
        """Verify that the proper Receipt page URL is returned."""
        order_number = 'ORDER1'
        url = EcommerceService().get_receipt_page_url(order_number)
        expected_url = '/checkout/receipt/{}'.format(order_number)
        self.assertEqual(url, expected_url)

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    def test_checkout_page_url(self):
        """ Verify the checkout page URL is properly constructed and returned. """
        url = EcommerceService().checkout_page_url(self.SKU)
        expected_url = 'http://ecommerce_url/test_basket/?sku={}'.format(self.SKU)
        self.assertEqual(url, expected_url)

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    @with_site_configuration(configuration=TEST_SITE_CONFIGURATION)
    def test_get_receipt_page_url_with_site_configuration(self):
        order_number = 'ORDER1'
        config = CommerceConfiguration.current()
        config.use_ecommerce_receipt_page = True
        config.save()

        receipt_page_url = EcommerceService().get_receipt_page_url(order_number)
        expected_url = '{ecommerce_root}{receipt_page_url}{order_number}'.format(
            ecommerce_root=settings.ECOMMERCE_PUBLIC_URL_ROOT,
            order_number=order_number,
            receipt_page_url=TEST_SITE_CONFIGURATION['ECOMMERCE_RECEIPT_PAGE_URL']
        )
        self.assertEqual(receipt_page_url, expected_url)
