"""
Third_party_auth integration tests using a mock version of the TestShib provider
"""
import unittest
import httpretty
from mock import patch

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from third_party_auth.tasks import fetch_saml_metadata
from third_party_auth.tests import testutil
from third_party_auth import pipeline
from student.tests.factories import UserFactory

from .base import IntegrationTestMixin


TESTSHIB_ENTITY_ID = 'https://idp.testshib.org/idp/shibboleth'
TESTSHIB_METADATA_URL = 'https://mock.testshib.org/metadata/testshib-providers.xml'
TESTSHIB_SSO_URL = 'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO'


def _make_entrypoint_url(auth_entry):
    """
    Builds TPA saml entrypoint with specified auth_entry value
    """
    return '/auth/login/tpa-saml/?auth_entry={auth_entry}&next=%2Fdashboard&idp=testshib'.format(auth_entry=auth_entry)

TPA_TESTSHIB_LOGIN_URL = _make_entrypoint_url('login')
TPA_TESTSHIB_REGISTER_URL = _make_entrypoint_url('register')
TPA_TESTSHIB_COMPLETE_URL = '/auth/complete/tpa-saml/'


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestShibIntegrationTest(IntegrationTestMixin, testutil.SAMLTestCase):
    """
    TestShib provider Integration Test, to test SAML functionality
    """
    PROVIDER_ID = "saml-testshib"
    PROVIDER_NAME = "TestShib"
    PROVIDER_BACKEND = "tpa-saml"

    USER_EMAIL = "myself@testshib.org"
    USER_NAME = "Me Myself And I"
    USER_USERNAME = "myself"

    def setUp(self):
        super(TestShibIntegrationTest, self).setUp()
        self.dashboard_page_url = reverse('dashboard')
        self.enable_saml(
            private_key=self._get_private_key(),
            public_key=self._get_public_key(),
            entity_id="https://saml.example.none",
        )
        # Mock out HTTP requests that may be made to TestShib:
        httpretty.enable()

        def metadata_callback(_request, _uri, headers):
            """ Return a cached copy of TestShib's metadata by reading it from disk """
            return (200, headers, self.read_data_file('testshib_metadata.xml'))
        httpretty.register_uri(httpretty.GET, TESTSHIB_METADATA_URL, content_type='text/xml', body=metadata_callback)
        self.addCleanup(httpretty.disable)
        self.addCleanup(httpretty.reset)

        # Configure the SAML library to use the same request ID for every request.
        # Doing this and freezing the time allows us to play back recorded request/response pairs
        uid_patch = patch('onelogin.saml2.utils.OneLogin_Saml2_Utils.generate_unique_id', return_value='TESTID')
        uid_patch.start()
        self.addCleanup(uid_patch.stop)
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.

    def test_login_before_metadata_fetched(self):
        self._configure_testshib_provider(fetch_metadata=False)
        # The user goes to the login page, and sees a button to login with TestShib:
        testshib_login_url = self._check_login_page()
        # The user clicks on the TestShib button:
        try_login_response = self.client.get(testshib_login_url)
        # The user should be redirected to back to the login page:
        self.assertEqual(try_login_response.status_code, 302)
        self.assertEqual(try_login_response['Location'], self.url_prefix + self.login_page_url)
        # When loading the login page, the user will see an error message:
        response = self.client.get(self.login_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Authentication with TestShib is currently unavailable.', response.content)

    def test_register(self):
        self._configure_testshib_provider()
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.
        # The user goes to the register page, and sees a button to register with TestShib:
        self._check_register_page()
        # The user clicks on the TestShib button:
        try_login_response = self.client.get(TPA_TESTSHIB_REGISTER_URL)
        # The user should be redirected to TestShib:
        self.assertEqual(try_login_response.status_code, 302)
        self.assertTrue(try_login_response['Location'].startswith(TESTSHIB_SSO_URL))
        # Now the user will authenticate with the SAML provider
        testshib_response = self._fake_testshib_login_and_return()
        # We should be redirected to the register screen since this account is not linked to an edX account:
        self.assertEqual(testshib_response.status_code, 302)
        self.assertEqual(testshib_response['Location'], self.url_prefix + self.register_page_url)
        register_response = self.client.get(self.register_page_url)
        # We'd now like to see if the "You've successfully signed into TestShib" message is
        # shown, but it's managed by a JavaScript runtime template, and we can't run JS in this
        # type of test, so we just check for the variable that triggers that message.
        self.assertIn('&#34;currentProvider&#34;: &#34;TestShib&#34;', register_response.content)
        self.assertIn('&#34;errorMessage&#34;: null', register_response.content)
        # Now do a crude check that the data (e.g. email) from the provider is displayed in the form:
        self.assertIn('&#34;defaultValue&#34;: &#34;myself@testshib.org&#34;', register_response.content)
        self.assertIn('&#34;defaultValue&#34;: &#34;Me Myself And I&#34;', register_response.content)
        # Now complete the form:
        ajax_register_response = self.client.post(
            reverse('user_api_registration'),
            {
                'email': 'myself@testshib.org',
                'name': 'Myself',
                'username': 'myself',
                'honor_code': True,
            }
        )
        self.assertEqual(ajax_register_response.status_code, 200)
        # Then the AJAX will finish the third party auth:
        continue_response = self.client.get(TPA_TESTSHIB_COMPLETE_URL)
        # And we should be redirected to the dashboard:
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(continue_response['Location'], self.url_prefix + self.dashboard_page_url)

        # Now check that we can login again:
        self.client.logout()
        self._verify_user_email('myself@testshib.org')
        self._test_return_login()

    def test_login(self):
        """ Configure TestShib before running the login test """
        self._configure_testshib_provider()
        super(TestShibIntegrationTest, self).test_login()

    def test_register(self):
        """ Configure TestShib before running the register test """
        self._configure_testshib_provider()
        super(TestShibIntegrationTest, self).test_register()

    def test_custom_form_does_not_link_by_email(self):
        self._configure_testshib_provider()
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.

        email = 'myself@testshib.org'
        UserFactory(username='myself', email=email, password='irrelevant')
        self._verify_user_email(email)
        self._assert_user_exists('myself', have_social=False)

        custom_url = pipeline.get_login_url('saml-testshib', 'custom1')
        self.client.get(custom_url)

        testshib_response = self._fake_testshib_login_and_return()

        # We should be redirected to the custom form since this account is not linked to an edX account, and
        # automatic linking is not enabled for custom1 entrypoint:
        self.assertEqual(testshib_response.status_code, 302)
        self.assertEqual(testshib_response['Location'], self.url_prefix + '/auth/custom_auth_entry')

    def test_custom_form_links_by_email(self):
        self._configure_testshib_provider()
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.

        email = 'myself@testshib.org'
        UserFactory(username='myself', email=email, password='irrelevant')
        self._verify_user_email(email)
        self._assert_user_exists('myself', have_social=False)

        custom_url = pipeline.get_login_url('saml-testshib', 'custom2')
        self.client.get(custom_url)

        testshib_response = self._fake_testshib_login_and_return()
        # We should be redirected to TPA-complete endpoint
        self.assertEqual(testshib_response.status_code, 302)
        self.assertEqual(testshib_response['Location'], self.url_prefix + TPA_TESTSHIB_COMPLETE_URL)

        complete_response = self.client.get(testshib_response['Location'])
        # And we should be redirected to the dashboard
        self.assertEqual(complete_response.status_code, 302)
        self.assertEqual(complete_response['Location'], self.url_prefix + self.dashboard_page_url)

        # And account should now be linked to social
        self._assert_user_exists('myself', have_social=True)

        # Now check that we can login again:
        self.client.logout()
        self._test_return_login()

    def _freeze_time(self, timestamp):
        """ Mock the current time for SAML, so we can replay canned requests/responses """
        now_patch = patch('onelogin.saml2.utils.OneLogin_Saml2_Utils.now', return_value=timestamp)
        now_patch.start()
        self.addCleanup(now_patch.stop)

    def _configure_testshib_provider(self, **kwargs):
        """ Enable and configure the TestShib SAML IdP as a third_party_auth provider """
        fetch_metadata = kwargs.pop('fetch_metadata', True)
        kwargs.setdefault('name', 'TestShib')
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('idp_slug', 'testshib')
        kwargs.setdefault('entity_id', TESTSHIB_ENTITY_ID)
        kwargs.setdefault('metadata_source', TESTSHIB_METADATA_URL)
        kwargs.setdefault('icon_class', 'fa-university')
        kwargs.setdefault('attr_email', 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6')  # eduPersonPrincipalName
        self.configure_saml_provider(**kwargs)

        if fetch_metadata:
            self.assertTrue(httpretty.is_enabled())
            num_changed, num_failed, num_total = fetch_saml_metadata()
            self.assertEqual(num_failed, 0)
            self.assertEqual(num_changed, 1)
            self.assertEqual(num_total, 1)

    def _fake_testshib_login_and_return(self):
        """ Mocked: the user logs in to TestShib and then gets redirected back """
        # The SAML provider (TestShib) will authenticate the user, then get the browser to POST a response:
        return self.client.post(
            TPA_TESTSHIB_COMPLETE_URL,
            content_type='application/x-www-form-urlencoded',
            data=self.read_data_file('testshib_response.txt'),
        )

    def _verify_user_email(self, email):
        """ Mark the user with the given email as verified """
        user = User.objects.get(email=email)
        user.is_active = True
        user.save()

    def do_provider_login(self, provider_redirect_url):
        """ Mocked: the user logs in to TestShib and then gets redirected back """
        # The SAML provider (TestShib) will authenticate the user, then get the browser to POST a response:
        self.assertTrue(provider_redirect_url.startswith(TESTSHIB_SSO_URL))
        return self.client.post(
            self.complete_url,
            content_type='application/x-www-form-urlencoded',
            data=self.read_data_file('testshib_response.txt'),
        )

    def _assert_user_exists(self, username, have_social=False, is_active=True):
        """
        Asserts user exists, checks activation status and social_auth links
        """
        user = User.objects.get(username=username)
        self.assertEqual(user.is_active, is_active)
        social_auths = user.social_auth.all()

        if have_social:
            self.assertEqual(1, len(social_auths))
            self.assertEqual('tpa-saml', social_auths[0].provider)
        else:
            self.assertEqual(0, len(social_auths))

    def _assert_user_does_not_exist(self, username):
        """ Asserts that user with specified username does not exist """
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(username=username)

    def _assert_account_created(self, username, email, full_name):
        """ Asserts that user with specified username exists, activated and have specified full name and email """
        user = User.objects.get(username=username)
        self.assertIsNotNone(user.profile)
        self.assertEqual(user.email, email)
        self.assertEqual(user.profile.name, full_name)
        self.assertTrue(user.is_active)
