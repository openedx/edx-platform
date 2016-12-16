"""
Tests for management command for enabling commerce configuration.
"""
from django.test import TestCase
from django.core.management import call_command

from commerce.models import CommerceConfiguration


class TestCommerceConfigurationCommand(TestCase):
    """
    Test django management command for enabling commerce configuration.
    """
    def test_commerce_configuration(self):
        """
        Test that commerce configuration is created properly.
        """
        call_command(
            "configure_commerce",
        )

        # Verify commerce configuration is enabled with appropriate values
        commerce_configuration = CommerceConfiguration.current()

        self.assertTrue(commerce_configuration.enabled)
        self.assertTrue(commerce_configuration.checkout_on_ecommerce_service)
        self.assertEqual(commerce_configuration.single_course_checkout_page, "/basket/single-item/")
        self.assertEqual(commerce_configuration.cache_ttl, 0)

        # Verify commerce configuration can be disabled from command
        call_command(
            "configure_commerce",
            '--disable',
        )

        commerce_configuration = CommerceConfiguration.current()
        self.assertFalse(commerce_configuration.enabled)

        # Verify commerce configuration can be disabled from command
        call_command(
            "configure_commerce",
            '--disable-checkout-on-ecommerce',
        )

        commerce_configuration = CommerceConfiguration.current()
        self.assertFalse(commerce_configuration.checkout_on_ecommerce_service)

    def test_site_associated_commerce_configuration(self):
        """
        This test is added here to fail when site_id field is added.

        This is done to make sure that this command gets updated once site_id field is added to
        CommerceConfiguration model.
        """
        self.assertFalse(
            hasattr(CommerceConfiguration, "site"),
            "Update configure_commerce command to account for site specific configurations.",
        )
