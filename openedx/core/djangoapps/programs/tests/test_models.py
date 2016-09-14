"""
Tests for models supporting Program-related functionality.
"""
import ddt
from mock import patch
from django.test import TestCase

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin


@ddt.ddt
@patch('config_models.models.cache.get', return_value=None)  # during tests, make every cache get a miss.
class ProgramsApiConfigTest(ProgramsApiConfigMixin, TestCase):
    """
    Tests for the ProgramsApiConfig model.
    """

    def test_default_state(self, _mock_cache):
        """
        Ensure the config stores empty values when no data has been inserted,
        and is completely disabled.
        """
        self.assertFalse(ProgramsApiConfig.is_enabled())
        api_config = ProgramsApiConfig.current()
        self.assertEqual(api_config.internal_service_url, '')
        self.assertEqual(api_config.public_service_url, '')
        self.assertEqual(api_config.api_version_number, None)
        self.assertFalse(api_config.is_student_dashboard_enabled)

    def test_created_state(self, _mock_cache):
        """
        Ensure the config stores correct values when created with them, but
        remains disabled.
        """
        self.create_config()
        self.assertFalse(ProgramsApiConfig.is_enabled())
        api_config = ProgramsApiConfig.current()
        self.assertEqual(api_config.internal_service_url, self.INTERNAL_URL)
        self.assertEqual(api_config.public_service_url, self.PUBLIC_URL)
        self.assertEqual(api_config.api_version_number, 1)
        self.assertFalse(api_config.is_student_dashboard_enabled)

    def test_api_urls(self, _mock_cache):
        """
        Ensure the api url methods return correct concatenations of service
        URLs and version numbers.
        """
        self.create_config()
        api_config = ProgramsApiConfig.current()
        self.assertEqual(api_config.internal_api_url, "{}api/v1/".format(self.INTERNAL_URL))
        self.assertEqual(api_config.public_api_url, "{}api/v1/".format(self.PUBLIC_URL))

    def test_is_student_dashboard_enabled(self, _mock_cache):
        """
        Ensure that is_student_dashboard_enabled only returns True when the
        current config has both 'enabled' and 'enable_student_dashboard' set to
        True.
        """
        self.assertFalse(ProgramsApiConfig.current().is_student_dashboard_enabled)

        self.create_config()
        self.assertFalse(ProgramsApiConfig.current().is_student_dashboard_enabled)

        self.create_config(enabled=True)
        self.assertFalse(ProgramsApiConfig.current().is_student_dashboard_enabled)

        self.create_config(enable_student_dashboard=True)
        self.assertFalse(ProgramsApiConfig.current().is_student_dashboard_enabled)

        self.create_config(enabled=True, enable_student_dashboard=True)
        self.assertTrue(ProgramsApiConfig.current().is_student_dashboard_enabled)

    @ddt.data(
        (True, 0),
        (False, 0),
        (False, 1),
    )
    @ddt.unpack
    def test_is_cache_enabled_returns_false(self, enabled, cache_ttl, _mock_cache):
        """Verify that the method 'is_cache_enabled' returns false if
        'cache_ttl' value is 0 or config is not enabled.
        """
        self.assertFalse(ProgramsApiConfig.current().is_cache_enabled)

        self.create_config(
            enabled=enabled,
            cache_ttl=cache_ttl
        )
        self.assertFalse(ProgramsApiConfig.current().is_cache_enabled)

    def test_is_cache_enabled_returns_true(self, _mock_cache):
        """"Verify that is_cache_enabled returns True when Programs is enabled
        and the cache TTL is greater than 0."
        """
        self.create_config(enabled=True, cache_ttl=10)
        self.assertTrue(ProgramsApiConfig.current().is_cache_enabled)
