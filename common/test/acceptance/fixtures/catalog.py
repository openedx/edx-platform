"""
Tools to create catalog-related data for use in bok choy tests.
"""
import json

import requests

from common.test.acceptance.fixtures import CATALOG_STUB_URL
from common.test.acceptance.fixtures.config import ConfigModelFixture


class CatalogFixture(object):
    """
    Interface to set up mock responses from the Catalog stub server.
    """
    def install_programs(self, data):
        """Set response data for the catalog's course run API."""
        key = 'catalog.programs'

        if isinstance(data, dict):
            key += '.' + data['uuid']

            requests.put(
                '{}/set_config'.format(CATALOG_STUB_URL),
                data={key: json.dumps(data)},
            )
        else:
            requests.put(
                '{}/set_config'.format(CATALOG_STUB_URL),
                data={key: json.dumps({'results': data})},
            )


class CatalogIntegrationMixin(object):
    """Mixin providing a method used to configure the catalog integration."""
    def set_catalog_integration(self, is_enabled=False, service_username=None):
        """Use this to change the catalog integration config model during tests."""
        ConfigModelFixture('/config/catalog', {
            'enabled': is_enabled,
            'internal_api_url': '{}/api/v1/'.format(CATALOG_STUB_URL),
            'cache_ttl': 0,
            'service_username': service_username,
        }).install()
