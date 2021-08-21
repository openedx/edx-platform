"""
Tests for Edly API serializers.
"""
import json
from urllib.parse import urljoin

from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory

from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory
from openedx.features.edly.api.serializers import UserSiteSerializer
from openedx.features.edly.tests.factories import EdlySubOrganizationFactory


class UserSiteSerializerTests(TestCase):

    def setUp(self):
        """
        Setup initial test data
        """
        super(UserSiteSerializerTests, self).setUp()
        self.request = RequestFactory().get('')
        self.edly_sub_org_of_user = EdlySubOrganizationFactory()
        self.context = {
            'request': self.request,
            'edly_sub_org_of_user': self.edly_sub_org_of_user,
        }
        self.serializer = UserSiteSerializer
        self.test_site_configuration = {
            'MOBILE_ENABLED': True,
            'MOBILE_APP_CONFIG': {
                'COURSE_SHARING_ENABLED': True,
                'COURSE_VIDEOS_ENABLED': False,
                'COURSE_DATES_ENABLED': False,
            },
            'BRANDING': {
                'favicon': 'fake-favicon-url',
                'logo': 'fake-logo-url',
                'logo-white': 'fake-logo-white-url',
            },
            'COLORS': {
                'primary': 'fake-color',
                'secondary': 'fake-color',
            },
            'SITE_NAME': self.edly_sub_org_of_user.lms_site.domain,
            'course_org_filter': self.edly_sub_org_of_user.get_edx_organizations,
            'contact_email': 'fake@example.com',
            'MKTG_URLS': {
                'ROOT': 'fake-root-url',
                'TOS': '/tos',
                'HONOR': '/honor',
                'PRIVACY': '/privacy',
            },
        }
        self.site_configuration = SiteConfigurationFactory(
            site=self.edly_sub_org_of_user.lms_site,
            enabled=True,
            site_values=self.test_site_configuration,
        )
        self.context['site_configuration'] = self.site_configuration.site_values.copy()

    def validate_url(self, url):
        """
        Validates a given string as url
        """
        validate = URLValidator()
        try:
            validate(url)
        except ValidationError:
            return False
        return True

    def get_expected_url(self):
        """
        Returns expected url of a site with protocol scheme if url is valid
        """
        protocol = 'https' if self.request.is_secure() else 'http'
        url = self.test_site_configuration['SITE_NAME']
        expected_url = '{}://{}'.format(protocol, url) if url else ''

        if self.validate_url(expected_url):
            return expected_url

        return ''

    def test_get_app_config(self):
        """
        Verify that `get_app_config` returns correct value.
        """
        serializer = self.serializer({}, context=self.context)

        app_config = json.loads(serializer.data['app_config'])

        for mobile_app_config_key, mobile_app_config_value in self.test_site_configuration['MOBILE_APP_CONFIG'].items():
            assert mobile_app_config_value == app_config.get(mobile_app_config_key)

        assert self.edly_sub_org_of_user.get_edx_organizations == app_config.get('ORGANIZATION_CODE')

        expected_api_host_url = self.get_expected_url()
        assert expected_api_host_url == app_config.get('API_HOST_URL')

        self.site_configuration.site_values['MOBILE_ENABLED'] = False
        self.site_configuration.save()
        self.context['site_configuration'] = self.site_configuration.site_values.copy()
        serializer = self.serializer({}, context=self.context)

        assert not serializer.data['app_config']

    def test_site_data(self):
        """
        Verify that `site_data` returns correct value.
        """
        serializer = self.serializer({}, context=self.context)
        for branding_key, branding_value in self.test_site_configuration['BRANDING'].items():
            assert branding_value == serializer.data['site_data'].get(branding_key)

        for color_key, color_value in self.test_site_configuration['COLORS'].items():
            assert color_value == serializer.data['site_data'].get(color_key)

        assert self.edly_sub_org_of_user.lms_site.name == serializer.data['site_data'].get('display_name')
        assert self.test_site_configuration['contact_email'] == serializer.data['site_data'].get('contact_email')

        mktg_urls = self.test_site_configuration['MKTG_URLS']
        expected_site_url = mktg_urls.get('ROOT')
        assert expected_site_url == serializer.data['site_data'].get('site_url')
        assert urljoin(mktg_urls.get('ROOT'), mktg_urls.get('TOS')) == serializer.data['site_data'].get('tos')
        assert urljoin(mktg_urls.get('ROOT'), mktg_urls.get('HONOR')) == serializer.data['site_data'].get('honor')
        assert urljoin(mktg_urls.get('ROOT'), mktg_urls.get('PRIVACY')) == serializer.data['site_data'].get('privacy')

    def test_mobile_enabled(self):
        """
        Verify that `mobile_enabled` returns correct value.
        """
        serializer = self.serializer({}, context=self.context)

        assert serializer.data['mobile_enabled']

        self.site_configuration.site_values['MOBILE_ENABLED'] = False
        self.site_configuration.save()
        self.context['site_configuration'] = self.site_configuration.site_values.copy()
        serializer = self.serializer({}, context=self.context)

        assert not serializer.data['mobile_enabled']
