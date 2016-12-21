"""Mixins to help test catalog integration."""
from openedx.core.djangoapps.catalog.models import CatalogIntegration


class CatalogIntegrationMixin(object):
    """Utility for working with the catalog service during testing."""

    DEFAULTS = {
        'enabled': True,
        'internal_api_url': 'https://catalog-internal.example.com/api/v1/',
        'cache_ttl': 0,
    }

    def create_catalog_integration(self, **kwargs):
        """Creates a new CatalogIntegration with DEFAULTS, updated with any provided overrides."""
        fields = dict(self.DEFAULTS, **kwargs)
        CatalogIntegration(**fields).save()

        return CatalogIntegration.current()
