"""Catalog model tests."""
import ddt
from django.test import TestCase
import mock

from openedx.core.djangoapps.catalog.tests import mixins


@ddt.ddt
# ConfigurationModels use the cache. Make every cache get a miss.
@mock.patch('config_models.models.cache.get', return_value=None)
class TestCatalogIntegration(mixins.CatalogIntegrationMixin, TestCase):
    """Tests covering the CatalogIntegration model."""

    @ddt.data(
        (0, False),
        (1, True),
    )
    @ddt.unpack
    def test_cache_control(self, cache_ttl, is_cache_enabled, _mock_cache):
        """Test the behavior of the property controlling whether API responses are cached."""
        catalog_integration = self.create_catalog_integration(cache_ttl=cache_ttl)
        self.assertEqual(catalog_integration.is_cache_enabled, is_cache_enabled)
