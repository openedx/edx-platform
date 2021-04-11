"""
Test cases for catalog_integrations command.
"""

from django.test import TestCase
from django.core.management import call_command, CommandError

from openedx.core.djangolib.testing.utils import CacheIsolationTestCase

from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.catalog.tests.mixins import CatalogIntegrationMixin


class TestCreateCatalogIntegrations(CatalogIntegrationMixin, CacheIsolationTestCase):
    """ Test the create_catalog_integrations command """

    def test_without_required(self):
        ''' Test that required values are supplied '''

        # test without service_username
        with self.assertRaises(CommandError):
            call_command(
                "create_catalog_integrations",
                "--internal_api_url", self.catalog_integration_defaults['internal_api_url'],
            )

        # test without internal_api_url
        with self.assertRaises(CommandError):
            call_command(
                "create_catalog_integrations",
                "--service_username", self.catalog_integration_defaults['service_username'],
            )

    def test_with_required(self):
        ''' Test with required arguments supplied'''

        initial = CatalogIntegration.current()

        # test with both required args
        call_command(
            "create_catalog_integrations",
            "--internal_api_url", self.catalog_integration_defaults['internal_api_url'],
            "--service_username", self.catalog_integration_defaults['service_username']
        )

        current = CatalogIntegration.current()

        # assert current has changed
        self.assertNotEqual(
            initial,
            current
        )

        self.assertEqual(
            current.enabled,
            False
        )
        self.assertEqual(
            current.internal_api_url,
            self.catalog_integration_defaults['internal_api_url']
        )

        self.assertEqual(
            current.service_username,
            self.catalog_integration_defaults['service_username']
        )

    def test_with_optional(self):
        ''' Test with optionals arguments supplied'''
        initial = CatalogIntegration.current()

        # test --enabled
        call_command(
            "create_catalog_integrations",
            "--internal_api_url", self.catalog_integration_defaults['internal_api_url'],
            "--service_username", self.catalog_integration_defaults['service_username'],
            "--enabled"
        )

        current = CatalogIntegration.current()

        # assert current has changed
        self.assertNotEqual(
            initial,
            current
        )

        self.assertEqual(
            current.enabled,
            True
        )
        self.assertEqual(
            current.internal_api_url,
            self.catalog_integration_defaults['internal_api_url']
        )

        self.assertEqual(
            current.service_username,
            self.catalog_integration_defaults['service_username']
        )

        # test with all args
        call_command(
            "create_catalog_integrations",
            "--internal_api_url", self.catalog_integration_defaults['internal_api_url'],
            "--service_username", self.catalog_integration_defaults['service_username'],
            "--enabled",
            "--cache_ttl", 500,
            "--long_term_cache_ttl", 500,
            "--page_size", 500
        )

        current = CatalogIntegration.current()

        # assert current has changed
        self.assertNotEqual(
            initial,
            current
        )

        self.assertEqual(
            current.enabled,
            True
        )
        self.assertEqual(
            current.internal_api_url,
            self.catalog_integration_defaults['internal_api_url']
        )

        self.assertEqual(
            current.service_username,
            self.catalog_integration_defaults['service_username']
        )

        self.assertEqual(
            current.cache_ttl,
            500
        )

        self.assertEqual(
            current.long_term_cache_ttl,
            500
        )
        self.assertEqual(
            current.page_size,
            500
        )
