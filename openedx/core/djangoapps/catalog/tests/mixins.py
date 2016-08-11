"""Mixins to help test catalog integration."""
import json
import urllib

import httpretty

from openedx.core.djangoapps.catalog.models import CatalogIntegration


class CatalogIntegrationMixin(object):
    """
    Utility for working with the catalog service during testing.
    """

    DEFAULTS = {
        'enabled': True,
        'internal_api_url': 'https://catalog-internal.example.com/api/v1/',
        'cache_ttl': 0,
    }

    def create_catalog_integration(self, **kwargs):
        """
        Creates a new CatalogIntegration with DEFAULTS, updated with any provided overrides.
        """
        fields = dict(self.DEFAULTS, **kwargs)
        CatalogIntegration(**fields).save()

        return CatalogIntegration.current()

    def register_catalog_course_run_response(self, course_keys, catalog_course_run_data):
        """
        Register a mock response for GET on the catalog course run endpoint.
        """
        httpretty.register_uri(
            httpretty.GET,
            "http://catalog.example.com:443/api/v1/course_runs/?keys={}&exclude_utm=1".format(
                urllib.quote_plus(",".join(course_keys))
            ),
            body=json.dumps({
                "results": catalog_course_run_data,
                "next": ""
            }),
            content_type='application/json',
            status=200
        )
