"""
Test site_configuration middleware.
"""


from django.test import TestCase
from django.test.client import Client
from django.test.utils import override_settings

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.site_configuration.tests.factories import SiteConfigurationFactory, SiteFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms


# NOTE: We set SESSION_SAVE_EVERY_REQUEST to True in order to make sure
# Sessions are always started on every request
@override_settings(SESSION_SAVE_EVERY_REQUEST=True)
@skip_unless_lms
class SessionCookieDomainTests(TestCase):
    """
    Tests regarding the session cookie management in the middleware for site_configuration
    """

    def setUp(self):
        super().setUp()
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
            site_values={
                "SESSION_COOKIE_DOMAIN": self.site.domain,
            }
        )

    def test_session_cookie_domain_no_override(self):
        """
        Test sessionid cookie when no override is set
        """
        response = self.client.get('/')
        assert 'test_site.localhost' not in str(response.cookies['sessionid'])
        assert 'Domain' not in str(response.cookies['sessionid'])


# NOTE: We set SESSION_SAVE_EVERY_REQUEST to True in order to make sure
# Sessions are always started on every request
@override_settings(SESSION_SAVE_EVERY_REQUEST=True)
@skip_unless_lms
class SessionCookieDomainSiteConfigurationOverrideTests(TestCase):
    """
    Tests regarding the session cookie management in the middlware for Microsites
    """

    def setUp(self):
        super().setUp()
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
            site_values={
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
        assert self.site.domain in str(response.cookies['sessionid'])
