# -*- coding: utf-8 -*-
"""
Test site_configuration middleware.
"""
import ddt
from mock import patch

from django.conf import settings
from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from student.tests.factories import UserFactory
from microsite_configuration.microsite import (
    get_backend,
)
from microsite_configuration.backends.base import BaseMicrositeBackend
from microsite_configuration.tests.tests import (
    DatabaseMicrositeTestCase,
    side_effect_for_get_value,
    MICROSITE_BACKENDS,
)
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


# NOTE: We set SESSION_SAVE_EVERY_REQUEST to True in order to make sure
# Sessions are always started on every request
# pylint: disable=no-member, protected-access
@ddt.ddt
@override_settings(SESSION_SAVE_EVERY_REQUEST=True)
@skip_unless_lms
class SessionCookieDomainMicrositeOverrideTests(DatabaseMicrositeTestCase):
    """
    Tests regarding the session cookie management in the middlware for Microsites
    """

    def setUp(self):
        super(SessionCookieDomainMicrositeOverrideTests, self).setUp()
        # Create a test client, and log it in so that it will save some session
        # data.
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.client = Client()
        self.client.login(username=self.user.username, password="password")

        self.site = SiteFactory.create(
            domain='testserver.fake',
            name='testserver.fake'
        )
        self.site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            values={
                "SESSION_COOKIE_DOMAIN": self.site.domain,
            }
        )

    @ddt.data(*MICROSITE_BACKENDS)
    def test_session_cookie_domain_no_override(self, site_backend):
        """
        Test sessionid cookie when no override is set
        """
        with patch('microsite_configuration.microsite.BACKEND',
                   get_backend(site_backend, BaseMicrositeBackend)):
            response = self.client.get('/')
            self.assertNotIn('test_site.localhost', str(response.cookies['sessionid']))
            self.assertNotIn('Domain', str(response.cookies['sessionid']))

    @ddt.data(*MICROSITE_BACKENDS)
    def test_session_cookie_domain_with_microsite_override(self, site_backend):
        """
        Makes sure that the cookie being set in a Microsite
        is the one specially overridden in configuration
        """
        with patch('microsite_configuration.microsite.BACKEND',
                   get_backend(site_backend, BaseMicrositeBackend)):
            response = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
            self.assertIn('test_site.localhost', str(response.cookies['sessionid']))

    @ddt.data(*MICROSITE_BACKENDS)
    def test_microsite_none_cookie_domain(self, site_backend):
        """
        Tests to make sure that a Microsite that specifies None for 'SESSION_COOKIE_DOMAIN' does not
        set a domain on the session cookie
        """
        with patch('microsite_configuration.microsite.get_value') as mock_get_value:
            mock_get_value.side_effect = side_effect_for_get_value('SESSION_COOKIE_DOMAIN', None)
            with patch('microsite_configuration.microsite.BACKEND',
                       get_backend(site_backend, BaseMicrositeBackend)):
                response = self.client.get('/', HTTP_HOST=settings.MICROSITE_TEST_HOSTNAME)
                self.assertNotIn('test_site.localhost', str(response.cookies['sessionid']))
                self.assertNotIn('Domain', str(response.cookies['sessionid']))


# NOTE: We set SESSION_SAVE_EVERY_REQUEST to True in order to make sure
# Sessions are always started on every request
# pylint: disable=no-member, protected-access
@override_settings(SESSION_SAVE_EVERY_REQUEST=True)
class SessionCookieDomainSiteConfigurationOverrideTests(TestCase):
    """
    Tests regarding the session cookie management in the middlware for Microsites
    """

    def setUp(self):
        super(SessionCookieDomainSiteConfigurationOverrideTests, self).setUp()
        # Create a test client, and log it in so that it will save some session data.
        self.user = UserFactory.create()
        self.user.set_password('password')
        self.user.save()
        self.site = SiteFactory.create(
            domain='testserver.fake',
            name='testserver.fake'
        )
        self.site_configuration = SiteConfigurationFactory.create(
            site=self.site,
            values={
                "SESSION_COOKIE_DOMAIN": self.site.domain,
            }
        )
        self.client = Client()
        self.client.login(username=self.user.username, password="password")

    def test_session_cookie_domain_with_site_configuration_override(self):
        """
        Makes sure that the cookie being set is for the overridden domain
        """
        response = self.client.get('/', HTTP_HOST=self.site.domain)
        self.assertIn(self.site.domain, str(response.cookies['sessionid']))
