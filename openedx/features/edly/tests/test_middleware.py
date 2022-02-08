"""
Unit tests for Middleware.
"""
from testfixtures import LogCapture
from django.conf import settings
from django.contrib import auth
from django.test import TestCase, modify_settings
from django.test.utils import override_settings
from django.test.client import Client, RequestFactory

from openedx.core.djangoapps.site_configuration.models import logger as site_configuration_logger
from openedx.core.djangoapps.site_configuration.tests.factories import (
    SiteConfigurationFactory,
    SiteFactory
)
from openedx.features.edly.cookies import _get_edly_user_info_cookie_string
from openedx.features.edly.tests.factories import (
    EdlySubOrganizationFactory,
    EdlyUserFactory
)

LOGGER_NAME = 'openedx.features.edly.middleware'


@modify_settings(
    MIDDLEWARE={
        'append': [
            'openedx.features.edly.middleware.EdlyOrganizationAccessMiddleware',
            'openedx.features.edly.middleware.SettingsOverrideMiddleware',
        ]
    }
)
class EdlyOrganizationAccessMiddlewareTests(TestCase):
    """
    Test Edly organization access middleware.
    """

    def setUp(self):
        self.user = EdlyUserFactory()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.site = SiteFactory()
        self.site_config = SiteConfigurationFactory(
            site=self.request.site,
            site_values={
                'MARKETING_SITE_ROOT': 'http://marketing.site',
                'DJANGO_SETTINGS_OVERRIDE': {'SITE_NAME': 'testserver.localhost'}
            }
        )

        self.client = Client(SERVER_NAME=self.request.site.domain)
        self.client.login(username=self.user.username, password='test')

    def test_disabled_edly_sub_orgainzation_access(self):
        """
        Test disabled Edly Organization access for a user.
        """
        EdlySubOrganizationFactory(lms_site=self.request.site, is_active=False)
        self.client.cookies.load(
            {
                settings.EDLY_USER_INFO_COOKIE_NAME: _get_edly_user_info_cookie_string(self.request)
            }
        )
        response = self.client.get('/')
        assert response.status_code != 200

    def test_user_with_edly_organization_access(self):
        """
        Test logged in user access based on user's linked edly sub organization.
        """
        EdlySubOrganizationFactory(lms_site=self.request.site)
        self.client.cookies.load(
            {
                settings.EDLY_USER_INFO_COOKIE_NAME: _get_edly_user_info_cookie_string(self.request)
            }
        )
        response = self.client.get('/', follow=True)
        assert response.status_code == 200

    @override_settings(FRONTEND_LOGOUT_URL=None)
    def test_user_without_edly_organization_access_and_without_frontend_logout_url(self):
        """
        Verify that logged in user gets redirected to logout page and valid log message response if user has no access without FRONTEND_LOGOUT_URL set.

        Test that logged in user gets redirected to logout page and valid log message if user has no access for
        request site's edly sub organization when FRONTEND_LOGOUT_URL is not set.
        """

        with LogCapture(LOGGER_NAME) as logger:
            response = self.client.get('/', follow=True)
            self.assertRedirects(
                response,
                '/logout',
                status_code=302,
                target_status_code=200,
                fetch_redirect_response=True
            )
            user = auth.get_user(self.client)
            assert not user.is_authenticated

            logger.check_present(
                (
                    LOGGER_NAME,
                    'ERROR',
                    'Edly user %s has no access for site %s.' % (self.user.email, self.request.site)
                )
            )

    @override_settings(FRONTEND_LOGOUT_URL='/logout')
    def test_user_without_edly_organization_access_and_with_frontend_logout_url(self):
        """
        Verify that logged in user gets redirected to logout page and valid log message response if user has no access with FRONTEND_LOGOUT_URL set.

        Test that logged in user gets redirected to logout page and valid log message if user has no access for
        request site's edly sub organization when FRONTEND_LOGOUT_URL is set.
        """

        with LogCapture(LOGGER_NAME) as logger:
            response = self.client.get('/', follow=True)
            logout_url = getattr(settings, 'FRONTEND_LOGOUT_URL', None)
            assert logout_url == '/logout'

            self.assertRedirects(
                response,
                logout_url,
                status_code=302,
                target_status_code=200,
                fetch_redirect_response=True
            )

            user = auth.get_user(self.client)
            assert not user.is_authenticated

            logger.check_present(
                (
                    LOGGER_NAME,
                    'ERROR',
                    'Edly user %s has no access for site %s.' % (self.user.email, self.request.site)
                )
            )

    def test_super_user_has_all_sites_access(self):
        """
        Test logged in super user has access to all sites.
        """
        edly_user = EdlyUserFactory(is_superuser=True)
        client = Client()
        client.login(username=edly_user.username, password='test')

        response = client.get('/', follow=True)
        assert response.status_code == 200

    def test_staff_has_all_sites_access(self):
        """
        Test logged in staff user has access to all sites.
        """
        edly_user = EdlyUserFactory(is_staff=True)
        client = Client()
        client.login(username=edly_user.username, password='test')

        response = client.get('/', follow=True)
        assert response.status_code == 200


@modify_settings(
    MIDDLEWARE={
        'append': [
            'openedx.features.edly.middleware.EdlyOrganizationAccessMiddleware',
            'openedx.features.edly.middleware.SettingsOverrideMiddleware',
        ]
    }
)
class SettingsOverrideMiddlewareTests(TestCase):
    """
    Tests settings override middleware for sites.
    """
    def setUp(self):
        """
        Create environment for settings override middleware tests.
        """
        self.user = EdlyUserFactory()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.site = SiteFactory()
        EdlySubOrganizationFactory(lms_site=self.request.site)

        self.client = Client(SERVER_NAME=self.request.site.domain)
        self.client.cookies.load(
            {
                settings.EDLY_USER_INFO_COOKIE_NAME: _get_edly_user_info_cookie_string(self.request)
            }
        )
        self.client.login(username=self.user.username, password='test')
        self.default_settings = {key: getattr(settings, key, None) for key in [
                'SITE_NAME', 'CMS_BASE', 'LMS_BASE', 'LMS_ROOT_URL', 'SESSION_COOKIE_DOMAIN',
                'LOGIN_REDIRECT_WHITELIST', 'DEFAULT_FEEDBACK_EMAIL', 'CREDENTIALS_PUBLIC_SERVICE_URL',
                'FEATURES',
            ]
        }

    def _assert_settings_values(self, expected_settings_values):
        """
        Checks if current settings values match expected settings values.
        """
        for config_key, expected_config_value in expected_settings_values.items():
            assert expected_config_value == getattr(settings, config_key, None)

    def test_settings_override_middleware_logs_warning_if_no_site_configuration_is_present(self):
        """
        Tests "SettingsOverrideMiddleware" logs warning if no site configuration is present.
        """
        with LogCapture(LOGGER_NAME) as logger:
            self.client.get('/', follow=True)
            logger.check_present(
                (
                    LOGGER_NAME,
                    'WARNING',
                    'Site ({site}) has no related site configuration.'.format(site=self.request.site)
                )
            )
            self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_logs_warning_if_site_configuration_has_no_values_set(self):
        """
        Tests "SettingsOverrideMiddleware" logs warning if site configuration has no values.
        """
        SiteConfigurationFactory(site=self.request.site)
        with LogCapture(LOGGER_NAME) as logger:
            self.client.get('/', follow=True)
            logger.check_present(
                (
                    LOGGER_NAME,
                    'WARNING',
                    'Site configuration for site ({site}) has no values set.'.format(site=self.request.site)
                )
            )
            self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_logs_warning_if_site_configuration_is_disabled(self):
        """
        Tests "SettingsOverrideMiddleware" logs warning if site configuration is disabled.
        """
        SiteConfigurationFactory(
            site=self.request.site,
            enabled=False,
            site_values={
                'MARKETING_SITE_ROOT': 'http://wordpress.edx.devstack.lms',
            }
        )
        with LogCapture(site_configuration_logger.name) as logger:
            self.client.get('/', follow=True)
            logger.check_present(
                (
                    site_configuration_logger.name,
                    'INFO',
                    'Site Configuration is not enabled for site ({site}).'.format(site=self.request.site)
                )
            )
            self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_logs_warning_for_empty_override(self):
        """
        Tests "SettingsOverrideMiddleware" logs warning if site configuration has no django settings override values.
        """
        SiteConfigurationFactory(
            site=self.request.site,
            site_values={
                'MARKETING_SITE_ROOT': 'http://wordpress.edx.devstack.lms',
            }
        )
        with LogCapture(LOGGER_NAME) as logger:
            self.client.get('/', follow=True)
            logger.check_present(
                (
                    LOGGER_NAME,
                    'WARNING',
                    'Site configuration for site ({site}) has no django settings overrides.'.format(site=self.request.site)
                )
            )
            self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_overrides_settings_correctly_if_dict(self):
        """
        Tests "SettingsOverrideMiddleware" correctly overrides dict django settings.

        Tests if a value being overriden through the middleware is a dict value,
        the value is being updated not replaced.
        """
        django_override_settings = {
            'FEATURES': {
                'PREVIEW_LMS_BASE': 'red.edx.devstack.lms'
            }
        }
        SiteConfigurationFactory(
            site=self.request.site,
            site_values={
                'DJANGO_SETTINGS_OVERRIDE': django_override_settings
            }
        )
        self._assert_settings_values(self.default_settings)
        self.client.get('/', follow=True)
        self.default_settings.get(list(django_override_settings.keys())[0]).update(
            **django_override_settings
        )
        self._assert_settings_values(self.default_settings)

    def test_settings_override_middleware_overrides_settings_correctly(self):
        """
        Tests "SettingsOverrideMiddleware" correctly overrides django settings.
        """
        django_override_settings = {
            'SITE_NAME': 'Test site',
            'CMS_BASE': 'localhost:8010',
            'LMS_BASE': 'localhost:8000',
            'LMS_ROOT_URL': 'http://edx.devstack.lms',
            'SESSION_COOKIE_DOMAIN': '.edx.devstack.lms',
            'LOGIN_REDIRECT_WHITELIST': [],
            'DEFAULT_FEEDBACK_EMAIL': 'test@example.com',
            'CREDENTIALS_PUBLIC_SERVICE_URL': 'http://credentials.edx.devstack.lms'
        }
        SiteConfigurationFactory(
            site=self.request.site,
            site_values={
                'DJANGO_SETTINGS_OVERRIDE': django_override_settings
            }
        )
        self._assert_settings_values(self.default_settings)
        self.client.get('/', follow=True)
        self._assert_settings_values(django_override_settings)
