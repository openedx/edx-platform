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
    def install_programs(self, programs):
        """Set response data for the catalog's course run API."""
        key = 'catalog.programs'

        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={key: json.dumps(programs)},
        )

    def install_course_run(self, course_run):
        """Set response data for the catalog's course run API."""
        key = 'catalog.{}'.format(course_run['key'])

        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={key: json.dumps(course_run)},
        )


class CatalogConfigMixin(object):
    """Mixin providing a method used to configure the catalog integration."""
    def set_catalog_configuration(self, is_enabled=False, service_url=CATALOG_STUB_URL):
        """Dynamically adjusts the catalog config model during tests."""
        ConfigModelFixture('/config/catalog', {
            'enabled': is_enabled,
            'internal_api_url': '{}/api/v1/'.format(service_url),
            'cache_ttl': 0,
        }).install()
