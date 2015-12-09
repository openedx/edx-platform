"""Tests for models supporting Program-related functionality."""
import ddt
from django.test import TestCase
import mock

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.tests.mixins import ProgramsApiConfigMixin


@ddt.ddt
# ConfigurationModels use the cache. Make every cache get a miss.
@mock.patch('config_models.models.cache.get', return_value=None)
class TestProgramsApiConfig(ProgramsApiConfigMixin, TestCase):
    """Tests covering the ProgramsApiConfig model."""
    def test_url_construction(self, _mock_cache):
        """Verify that URLs returned by the model are constructed correctly."""
        programs_config = self.create_config()

        self.assertEqual(
            programs_config.internal_api_url,
            programs_config.internal_service_url.strip('/') + '/api/v{}/'.format(programs_config.api_version_number)
        )
        self.assertEqual(
            programs_config.public_api_url,
            programs_config.public_service_url.strip('/') + '/api/v{}/'.format(programs_config.api_version_number)
        )

        authoring_app_config = programs_config.authoring_app_config

        self.assertEqual(
            authoring_app_config.js_url,
            programs_config.public_service_url.strip('/') + programs_config.authoring_app_js_path
        )
        self.assertEqual(
            authoring_app_config.css_url,
            programs_config.public_service_url.strip('/') + programs_config.authoring_app_css_path
        )

    @ddt.data(
        (0, False),
        (1, True),
    )
    @ddt.unpack
    def test_cache_control(self, cache_ttl, is_cache_enabled, _mock_cache):
        """Verify the behavior of the property controlling whether API responses are cached."""
        programs_config = self.create_config(cache_ttl=cache_ttl)
        self.assertEqual(programs_config.is_cache_enabled, is_cache_enabled)

    def test_is_student_dashboard_enabled(self, _mock_cache):
        """
        Verify that the property controlling display on the student dashboard is only True
        when configuration is enabled and all required configuration is provided.
        """
        programs_config = self.create_config(enabled=False)
        self.assertFalse(programs_config.is_student_dashboard_enabled)

        programs_config = self.create_config(enable_student_dashboard=False)
        self.assertFalse(programs_config.is_student_dashboard_enabled)

        programs_config = self.create_config()
        self.assertTrue(programs_config.is_student_dashboard_enabled)

    def test_is_studio_tab_enabled(self, _mock_cache):
        """
        Verify that the property controlling display of the Studio tab is only True
        when configuration is enabled and all required configuration is provided.
        """
        programs_config = self.create_config(enabled=False)
        self.assertFalse(programs_config.is_studio_tab_enabled)

        programs_config = self.create_config(enable_studio_tab=False)
        self.assertFalse(programs_config.is_studio_tab_enabled)

        programs_config = self.create_config(authoring_app_js_path='', authoring_app_css_path='')
        self.assertFalse(programs_config.is_studio_tab_enabled)

        programs_config = self.create_config()
        self.assertTrue(programs_config.is_studio_tab_enabled)
