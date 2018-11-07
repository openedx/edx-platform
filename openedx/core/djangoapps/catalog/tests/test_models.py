"""Catalog model tests."""
import ddt
import mock
from django.test import TestCase, override_settings

from openedx.core.djangoapps.catalog.tests import mixins
from openedx.core.djangoapps.site_configuration.tests.test_util import with_site_configuration

COURSE_CATALOG_API_URL = 'https://api.example.com/v1/'


@ddt.ddt
# ConfigurationModels use the cache. Make every cache get a miss.
@mock.patch('config_models.models.cache.get', return_value=None)
class TestCatalogIntegration(mixins.CatalogIntegrationMixin, TestCase):
    """Tests covering the CatalogIntegration model."""

    def assert_get_internal_api_url_value(self, expected):
        """ Asserts the value of get_internal_api_url matches the expected value. """
        catalog_integration = self.create_catalog_integration()
        self.assertEqual(catalog_integration.get_internal_api_url(), expected)

    @ddt.data(
        (0, False),
        (1, True),
    )
    @ddt.unpack
    def test_cache_control(self, cache_ttl, is_cache_enabled, _mock_cache):
        """Test the behavior of the property controlling whether API responses are cached."""
        catalog_integration = self.create_catalog_integration(cache_ttl=cache_ttl)
        self.assertEqual(catalog_integration.is_cache_enabled, is_cache_enabled)

    @override_settings(COURSE_CATALOG_API_URL=COURSE_CATALOG_API_URL)
    def test_get_internal_api_url(self, _mock_cache):
        """ Requests made without a microsite should return the value from settings. """
        self.assert_get_internal_api_url_value(COURSE_CATALOG_API_URL)
        catalog_integration = self.create_catalog_integration()
        self.assertEqual(catalog_integration.get_internal_api_url(), COURSE_CATALOG_API_URL)

    @override_settings(COURSE_CATALOG_API_URL=COURSE_CATALOG_API_URL)
    @with_site_configuration(configuration={})
    def test_get_internal_api_url_without_microsite_override(self, _mock_cache):
        """ Requests made to microsites that do not have COURSE_CATALOG_API_URL overridden should
        return the default value from settings. """
        self.assert_get_internal_api_url_value(COURSE_CATALOG_API_URL)

    @override_settings(COURSE_CATALOG_API_URL=COURSE_CATALOG_API_URL)
    @with_site_configuration(configuration={'COURSE_CATALOG_API_URL': 'foo'})
    def test_get_internal_api_url_with_microsite_override(self, _mock_cache):
        """ If a microsite has overridden the value of COURSE_CATALOG_API_URL, the overridden
        value should be returned. """
        self.assert_get_internal_api_url_value('foo')
