"""
Third_party_auth integration tests using a mock version of the TestShib provider
"""
import unittest
import httpretty
from mock import patch

from third_party_auth.tasks import fetch_saml_metadata
from third_party_auth.tests import testutil

from .base import IntegrationTestMixin


TESTSHIB_ENTITY_ID = 'https://idp.testshib.org/idp/shibboleth'
TESTSHIB_METADATA_URL = 'https://mock.testshib.org/metadata/testshib-providers.xml'
TESTSHIB_SSO_URL = 'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO'


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

    def test_login(self):
        """ Configure TestShib before running the login test """
        self._configure_testshib_provider()
        super(TestShibIntegrationTest, self).test_login()

    def test_register(self):
        """ Configure TestShib before running the register test """
        self._configure_testshib_provider()
        super(TestShibIntegrationTest, self).test_register()

    def test_autoprovision_from_login(self):
        self._configure_testshib_provider(autoprovision_account=True)
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.

        # check that we don't have a user we're autoprovisioning account for
        self._assert_user_does_not_exist('myself')

        # The user goes to the register page, and sees a button to register with TestShib:
        self._check_login_page()

        self._test_autoprovision(TPA_TESTSHIB_LOGIN_URL)

    def test_autoprovision_from_register(self):
        self._configure_testshib_provider(autoprovision_account=True)
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.

        # check that we don't have a user we're autoprovisioning account for
        self._assert_user_does_not_exist('myself')

        # The user goes to the register page, and sees a button to register with TestShib:
        self._check_register_page()

        self._test_autoprovision(TPA_TESTSHIB_REGISTER_URL)

    def _test_autoprovision(self, entry_point):
        """ Actual autoprovision code """
        # The user clicks on the TestShib button:
        try_entry_response = self.client.get(entry_point)
        # The user should be redirected to TestShib:
        self.assertEqual(try_entry_response.status_code, 302)
        self.assertTrue(try_entry_response['Location'].startswith(TESTSHIB_SSO_URL))

        # Now the user will authenticate with the SAML provider
        self._fake_testshib_login_and_return()

        # Then there's one more redirect to set logged_in cookie
        continue_response = self.client.get(TPA_TESTSHIB_COMPLETE_URL)

        # We should be redirected to the dashboard screen since profile should be created and logged in
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(continue_response['Location'], self.url_prefix + self.dashboard_page_url)

        # assert account is created and activated
        self._assert_account_created(username='myself', email='myself@testshib.org', full_name='Me Myself And I')

        # Now check that we can login again:
        self.client.logout()
        self._test_return_login()

    def _test_return_login(self):
        """ Test logging in to an account that is already linked. """
        # Make sure we're not logged in:
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 302)
        # The user goes to the login page, and sees a button to login with TestShib:
        self._check_login_page()
        # The user clicks on the TestShib button:
        try_login_response = self.client.get(TPA_TESTSHIB_LOGIN_URL)
        # The user should be redirected to TestShib:
        self.assertEqual(try_login_response.status_code, 302)
        self.assertTrue(try_login_response['Location'].startswith(TESTSHIB_SSO_URL))
        # Now the user will authenticate with the SAML provider
        login_response = self._fake_testshib_login_and_return()
        # There will be one weird redirect required to set the login cookie:
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response['Location'], self.url_prefix + TPA_TESTSHIB_COMPLETE_URL)
        # And then we should be redirected to the dashboard:
        login_response = self.client.get(TPA_TESTSHIB_COMPLETE_URL)
        self.assertEqual(login_response.status_code, 302)
        self.assertEqual(login_response['Location'], self.url_prefix + reverse('dashboard'))
        # Now we are logged in:
        dashboard_response = self.client.get(reverse('dashboard'))
        self.assertEqual(dashboard_response.status_code, 200)

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
        kwargs.setdefault('autoprovision_account', False)
        self.configure_saml_provider(**kwargs)

        if fetch_metadata:
            self.assertTrue(httpretty.is_enabled())
            num_changed, num_failed, num_total = fetch_saml_metadata()
            self.assertEqual(num_failed, 0)
            self.assertEqual(num_changed, 1)
            self.assertEqual(num_total, 1)

    def do_provider_login(self, provider_redirect_url):
        """ Mocked: the user logs in to TestShib and then gets redirected back """
        # The SAML provider (TestShib) will authenticate the user, then get the browser to POST a response:
        self.assertTrue(provider_redirect_url.startswith(TESTSHIB_SSO_URL))
        return self.client.post(
            self.complete_url,
            content_type='application/x-www-form-urlencoded',
            data=self.read_data_file('testshib_response.txt'),
        )

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
