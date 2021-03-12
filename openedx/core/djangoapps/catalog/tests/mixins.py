"""Mixins to help test catalog integration."""


from openedx.core.djangoapps.catalog.models import CatalogIntegration


class CatalogIntegrationMixin(object):
    """Utility for working with the catalog service during testing."""

    catalog_integration_defaults = {
        'enabled': True,
        'internal_api_url': 'https://catalog-internal.example.com/api/v1/',
        'cache_ttl': 0,
        'service_username': 'lms_catalog_service_user',
        'page_size': 20,
    }

    def create_catalog_integration(self, **kwargs):
        """
        Creates a new CatalogIntegration with catalog_integration_defaults,
        updated with any provided overrides.
        """
        fields = dict(self.catalog_integration_defaults, **kwargs)
        CatalogIntegration(**fields).save()

        return CatalogIntegration.current()
