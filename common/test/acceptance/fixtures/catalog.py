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
    @classmethod
    def install_programs(cls, programs):
        """
        Stub the discovery service's program list and detail API endpoints.

        Arguments:
            programs (list): A list of programs. Both list and detail endpoints
                will be stubbed using data from this list.
        """
        key = 'catalog.programs'

        uuids = []
        for program in programs:
            uuid = program['uuid']
            uuids.append(uuid)

            program_key = '{base}.{uuid}'.format(base=key, uuid=uuid)
            requests.put(
                '{}/set_config'.format(CATALOG_STUB_URL),
                data={program_key: json.dumps(program)},
            )

        # Stub list endpoint as if the uuids_only query param had been passed.
        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={key: json.dumps(uuids)},
        )

    @classmethod
    def install_pathways(cls, pathways):
        """
        Stub the discovery service's credit pathways API endpoint

        Arguments:
             pathways (list): A list of credit pathways. List endpoint will be stubbed using data from this list.
        """
        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={'catalog.pathways': json.dumps({'results': pathways, 'next': None})}
        )

    @classmethod
    def install_program_types(cls, program_types):
        """
        Stub the discovery service's program type list API endpoints.

        Arguments:
            program_types (list): A list of program types. List endpoint will be stubbed using data from this list.
        """
        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={'catalog.programs_types': json.dumps(program_types)},
        )

    @classmethod
    def install_course_runs(cls, course_runs):
        """
        Stub the discovery service's course run list API endpoints.

        Arguments:
            course_runs (list): A list of course runs. List endpoint will be stubbed using data from this list.
        """
        requests.put(
            '{}/set_config'.format(CATALOG_STUB_URL),
            data={'catalog.course_runs': json.dumps({'results': course_runs, 'next': None})}
        )


class CatalogIntegrationMixin(object):
    """Mixin providing a method used to configure the catalog integration."""

    @classmethod
    def set_catalog_integration(cls, is_enabled=False, service_username=None):
        """Use this to change the catalog integration config model during tests."""
        ConfigModelFixture('/config/catalog', {
            'enabled': is_enabled,
            'internal_api_url': '{}/api/v1/'.format(CATALOG_STUB_URL),
            'cache_ttl': 0,
            'service_username': service_username,
        }).install()
