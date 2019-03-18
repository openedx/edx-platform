"""
Tests for site configuration's Tahoe customizations.
"""
from mock import patch
import unittest

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.contrib.sites.models import Site
from django.test.utils import override_settings

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory


# TODO: This is an integration test, try to make it less so and more of a unit-test.
@override_settings(
    COMPREHENSIVE_THEME_DIRS=['/edx/src/themes'],
    ENABLE_COMPREHENSIVE_THEMING=True,
    DEFAULT_SITE_THEME='edx-theme-codebase',
)
class SiteConfigurationTests(TestCase):
    """
    Tests for SiteConfiguration and its signals/receivers.
    """
    domain = 'example-site.tahoe.appsembler.com'
    name = 'Example Tahoe Site'

    test_config = {
        "university": "Tahoe University",
        "platform_name": name,
        "SITE_NAME": domain,
        "course_org_filter": "TahoeX",
        "css_overrides_file": "test/css/{domain}.css".format(domain=domain),
        "ENABLE_MKTG_SITE": False,
        "ENABLE_THIRD_PARTY_AUTH": False,
        "course_about_show_social_links": False,
    }

    @classmethod
    def setUpClass(cls):
        super(SiteConfigurationTests, cls).setUpClass()
        cls.site, _ = Site.objects.get_or_create(
            domain=cls.test_config['SITE_NAME'],
            name=cls.test_config['SITE_NAME'],
        )

    def test_site_configuration_compile_sass(self):
        """
        Test that and entry is added to SiteConfigurationHistory model each time a new
        SiteConfiguration is added.
        """
        # add SiteConfiguration to database
        site_configuration = SiteConfigurationFactory.build(
            site=self.site,
        )

        site_configuration.save()
