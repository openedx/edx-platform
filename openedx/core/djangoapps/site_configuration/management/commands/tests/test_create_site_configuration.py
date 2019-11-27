"""
Test create_site_configuration management command
"""
import json

from django.contrib.sites.models import Site
from django.core.management import call_command
from django.test import TestCase
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration


class TestCreateSiteConfiguration(TestCase):
    """ Test create_site_configuration command """
    def setUp(self):
        super(TestCreateSiteConfiguration, self).setUp()
        self.site_domain = 'example.com'
        self.input_configuration = {
            'FEATURE_FLAG': True,
            'SERVICE_URL': 'https://foo.bar'
        }

    def _validate_site_configuration(self, site):
        site_configuration = SiteConfiguration.objects.get(site_id=site.id)
        self.assertDictEqual(site_configuration.values, self.input_configuration)

    def test_create_site_and_config(self):
        call_command(
            'create_site_configuration',
            self.site_domain,
            '--configuration', json.dumps(self.input_configuration),
        )

        site = Site.objects.get(domain__contains=self.site_domain)
        self.assertEquals(site.name, self.site_domain)
        self.assertEquals(site.domain, self.site_domain)

        self._validate_site_configuration(site)

    def test_create_for_existing_site(self):
        site, created = Site.objects.get_or_create(  # pylint: disable=unused-variable
            name=self.site_domain,
            domain=self.site_domain,
        )

        call_command(
            'create_site_configuration',
            self.site_domain,
            '--configuration', json.dumps(self.input_configuration),
        )

        self.assertEqual(len(Site.objects.filter(domain__contains=self.site_domain)), 1)
        self._validate_site_configuration(site)
