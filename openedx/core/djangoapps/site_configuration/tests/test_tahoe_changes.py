"""
Tests for site configuration's Tahoe customizations.
"""
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sites.models import Site
from django.test import TestCase
from django.test.utils import override_settings
from mock import Mock

from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory


@override_settings(
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

        cls.scheme = urlsplit(settings.LMS_ROOT_URL).scheme
        cls.expected_site_root_url = '{scheme}://{domain}'.format(
            scheme=cls.scheme, domain=cls.domain)

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

    def test_get_value(self):
        """
        Test that get_value returns correct value for Tahoe custom keys.
        """
        # add SiteConfiguration to database
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            site_values=self.test_config
        )

        # Make sure entry is saved and retrieved correctly
        self.assertEqual(site_configuration.get_value("PLATFORM_NAME"),
                         self.test_config['platform_name'])
        self.assertEqual(site_configuration.get_value("LMS_ROOT_URL"),
                         self.expected_site_root_url)
        self.assertTrue(site_configuration.get_value('ACTIVATION_EMAIL_SUPPORT_LINK'))
        self.assertTrue(site_configuration.get_value('ACTIVATION_EMAIL_SUPPORT_LINK').endswith('/help'))
        self.assertTrue(site_configuration.get_value('PASSWORD_RESET_SUPPORT_LINK'))
        self.assertTrue(site_configuration.get_value('PASSWORD_RESET_SUPPORT_LINK').endswith('/help'))

    def test_get_value_for_org(self):
        """
        Test that get_value_for_org returns correct value for Tahoe custom keys.
        """
        # add SiteConfiguration to database
        SiteConfigurationFactory.create(
            site=self.site,
            site_values=self.test_config
        )

        # Test that LMS_ROOT_URL is assigned to the SiteConfiguration on creation
        self.assertEqual(
            SiteConfiguration.get_value_for_org(
                self.test_config['course_org_filter'], 'LMS_ROOT_URL'),
            self.expected_site_root_url
        )


@override_settings(
    ENABLE_COMPREHENSIVE_THEMING=True,
)
class SiteConfigAPIClientTests(TestCase):
    """
    Tests for SiteConfiguration and its signals/receivers.
    """
    domain = 'example-site.tahoe.appsembler.com'
    name = 'API Adapter Platform'

    test_config = {
        "university": "Tahoe University",
        "platform_name": name,
        "SITE_NAME": domain,
        "course_org_filter": "TahoeX",
        "ENABLE_MKTG_SITE": False,
        "ENABLE_THIRD_PARTY_AUTH": False,
        "course_about_show_social_links": False,
    }

    sass_variables = [
        ["$brand-primary-color", ["#0090C1", "#0090C1"]],
        ["$brand-accent-color", ["#7f8c8d", "#7f8c8d"]],
    ]

    about_page = {
        'title': 'About page from site configuration service',
    }

    @classmethod
    def setUpClass(cls):
        super(SiteConfigAPIClientTests, cls).setUpClass()
        cls.site, _ = Site.objects.get_or_create(
            domain=cls.test_config['SITE_NAME'],
            name=cls.test_config['SITE_NAME'],
        )
        cls.api_adapter = Mock(
            get_value=cls.test_config.get,
            get_amc_v1_theme_css_variables=Mock(return_value=cls.sass_variables),
            get_amc_v1_page=Mock(return_value=cls.about_page),
        )

    def test_get_value_with_adapter(self):
        """
        Ensure api_adapter is used for `get_value()`.
        """
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            site_values={},
        )
        site_configuration.api_adapter = self.api_adapter
        site_configuration.save()
        assert site_configuration.get_value('platform_name') == 'API Adapter Platform'

    def test_formatted_sass_variables_with_adapter(self):
        """
        Ensure api_adapter is used for `_formatted_sass_variables()`.
        """
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            site_values={},
        )
        site_configuration.api_adapter = self.api_adapter
        assert site_configuration._formatted_sass_variables()

    def test_page_content_without_adapter(self):
        """
        Test `get_page_content()` without the SiteConfig adapter.
        """
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            page_elements={
                'about': {
                    'title': 'About page in Django model.',
                },
            },
        )
        assert site_configuration.get_page_content('about') == {
            'title': 'About page in Django model.',
        }

    def test_page_content_with_adapter(self):
        """
        Ensure `get_page_content()` uses the SiteConfig adapter when available.
        """
        site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            page_elements={
                'about': {
                    'title': 'About page in Django model.',
                },
            },
        )
        site_configuration.api_adapter = self.api_adapter
        assert site_configuration.get_page_content('about') == {
            'title': 'About page from site configuration service',
        }
