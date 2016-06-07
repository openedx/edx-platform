"""Tests of commerce utilities."""
from django.test import TestCase
from django.test.utils import override_settings
from mock import patch

from commerce.utils import audit_log, EcommerceService
from commerce.models import CommerceConfiguration
from django.test.client import RequestFactory
from student.tests.factories import UserFactory


def update_commerce_config(enabled=False, checkout_page='/test_basket/'):
    """ Enable / Disable CommerceConfiguration model """
    CommerceConfiguration.objects.create(
        checkout_on_ecommerce_service=enabled,
        single_course_checkout_page=checkout_page
    )


class AuditLogTests(TestCase):
    """Tests of the commerce audit logging helper."""
    @patch('commerce.utils.log')
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
    def test_payment_page_url(self):
        """Verify that the proper URL is returned."""
        url = EcommerceService().payment_page_url()
        self.assertEqual(url, 'http://ecommerce_url/test_basket/')

    @override_settings(ECOMMERCE_PUBLIC_URL_ROOT='http://ecommerce_url')
    def test_checkout_page_url(self):
        """ Verify the checkout page URL is properly constructed and returned. """
        url = EcommerceService().checkout_page_url(self.SKU)
        expected_url = 'http://ecommerce_url/test_basket/?sku={}'.format(self.SKU)
        self.assertEqual(url, expected_url)
