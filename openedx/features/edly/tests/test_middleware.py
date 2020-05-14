"""
Unit tests for Middleware.
"""
from testfixtures import LogCapture
from django.conf import settings
from django.test import TestCase
from django.test.client import Client, RequestFactory

from openedx.features.edly import cookies
from openedx.features.edly.tests.factories import (
    EdlySubOrganizationFactory,
    EdlyUserFactory,
    SiteFactory,
)

LOGGER_NAME = 'openedx.features.edly.middleware'


class EdlyOrganizationAccessMiddlewareTests(TestCase):

    def setUp(self):
        self.user = EdlyUserFactory()
        self.request = RequestFactory().get('/')
        self.request.user = self.user
        self.request.site = SiteFactory()

        self.client = Client(SERVER_NAME=self.request.site.domain)
        self.client.login(username=self.user.username, password='test')

    def test_user_with_edly_organization_access(self):
        """
        Test logged in user access based on user's linked edly sub organization.
        """
        EdlySubOrganizationFactory(lms_site=self.request.site)
        self.client.cookies.load(
            {
                settings.EDLY_USER_INFO_COOKIE_NAME: cookies._get_edly_user_info_cookie_string(self.request)
            }
        )

        response = self.client.get('/', follow=True)
        assert response.status_code == 200

    def test_user_without_edly_organization_access(self):
        """
        Verify that logged in user gets valid error and log message response if user has no access.

        Test that logged in user gets 404 and valid log message if user has no access for
        request site's edly sub organization.
        """

        with LogCapture(LOGGER_NAME) as logger:
            response = self.client.get('/', follow=True)
            assert response.status_code == 404

            logger.check(
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
