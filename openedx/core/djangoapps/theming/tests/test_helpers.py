"""
Test helpers for Comprehensive Theming.
"""
from django.test import TestCase
from mock import patch

from openedx.core.djangoapps.theming import helpers


class ThemingHelpersTests(TestCase):
    """
    Make sure some of the theming helper functions work
    """

    def test_get_value_returns_override(self):
        """
        Tests to make sure the get_value() operation returns a combined dictionary consisting
        of the base container with overridden keys from the microsite configuration
        """
        with patch('microsite_configuration.microsite.get_value') as mock_get_value:
            override_key = 'JWT_ISSUER'
            override_value = 'testing'
            mock_get_value.return_value = {override_key: override_value}
            jwt_auth = helpers.get_value('JWT_AUTH')
            self.assertEqual(jwt_auth[override_key], override_value)
