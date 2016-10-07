"""
Third_party_auth integration tests using a mock version of the TestShib provider
"""
import ddt
import unittest
import httpretty
from mock import patch
from social.apps.django_app.default.models import UserSocialAuth

from third_party_auth.saml import log as saml_log
from third_party_auth.tasks import fetch_saml_metadata
from third_party_auth.tests import testutil

from .base import IntegrationTestMixin


TESTSHIB_ENTITY_ID = 'https://idp.testshib.org/idp/shibboleth'
TESTSHIB_METADATA_URL = 'https://mock.testshib.org/metadata/testshib-providers.xml'
TESTSHIB_METADATA_URL_WITH_CACHE_DURATION = 'https://mock.testshib.org/metadata/testshib-providers-cache.xml'
TESTSHIB_SSO_URL = 'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO'


@ddt.ddt
@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestShibIntegrationTest(IntegrationTestMixin, testutil.SAMLTestCase):
    """
    TestShib provider Integration Test, to test SAML functionality
    """
    PROVIDER_ID = "saml-testshib"
    PROVIDER_NAME = "TestShib"
    PROVIDER_BACKEND = "tpa-saml"
    PROVIDER_IDP_SLUG = "testshib"

    USER_EMAIL = "myself@testshib.org"
    USER_NAME = "Me Myself And I"
    USER_USERNAME = "myself"

    def setUp(self):
        super(TestShibIntegrationTest, self).setUp()
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

        def cache_duration_metadata_callback(_request, _uri, headers):
            """Return a cached copy of TestShib's metadata with a cacheDuration attribute"""
            return (200, headers, self.read_data_file('testshib_metadata_with_cache_duration.xml'))

        httpretty.register_uri(
            httpretty.GET,
            TESTSHIB_METADATA_URL_WITH_CACHE_DURATION,
            content_type='text/xml',
            body=cache_duration_metadata_callback
        )
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

    def test_register_with_data_sharing_consent(self):
        """
        Configure TestShib to require data sharing consent before running the registration test
        """
        self._configure_testshib_provider(require_data_sharing_consent=True)
        super(TestShibIntegrationTest, self).test_register(data_sharing_consent=True)

    def test_registration_not_allowed_without_data_sharing_consent(self):
        """
        Configure TestShib to require data sharing consent, but don't provide
        consent when registering
        """
        self._configure_testshib_provider(require_data_sharing_consent=True)
        # The user goes to the register page, and sees a button to register with the provider:
        provider_register_url = self._check_register_page()
        # The user clicks on the Dummy button:
        try_login_response = self.client.get(provider_register_url)
        # The user should be redirected to the provider's login page:
        self.assertEqual(try_login_response.status_code, 302)
        provider_response = self.do_provider_login(try_login_response['Location'])
        # We should be redirected to the register screen since this account is not linked to an edX account:
        self.assertEqual(provider_response.status_code, 302)
        self.assertEqual(provider_response['Location'], self.url_prefix + self.register_page_url)
        register_response = self.client.get(self.register_page_url)
        tpa_context = register_response.context["data"]["third_party_auth"]
        self.assertEqual(tpa_context["errorMessage"], None)
        # Check that the "You've successfully signed into [PROVIDER_NAME]" message is shown.
        self.assertEqual(tpa_context["currentProvider"], self.PROVIDER_NAME)
        # Check that the data (e.g. email) from the provider is displayed in the form:
        form_data = register_response.context['data']['registration_form_desc']
        form_fields = {field['name']: field for field in form_data['fields']}
        self.assertEqual(form_fields['email']['defaultValue'], self.USER_EMAIL)
        self.assertEqual(form_fields['name']['defaultValue'], self.USER_NAME)
        self.assertEqual(form_fields['username']['defaultValue'], self.USER_USERNAME)
        registration_values = {
            'email': 'email-edited@tpa-test.none',
            'name': 'My Customized Name',
            'username': 'new_username',
            'honor_code': True,
            'data_sharing_consent': False
        }
        # Now complete the form:
        ajax_register_response = self.client.post(
            reverse('user_api_registration'),
            registration_values
        )
        self.assertEqual(ajax_register_response.status_code, 400)

    def test_login_records_attributes(self):
        """
        Test that attributes sent by a SAML provider are stored in the UserSocialAuth table.
        """
        self.test_login()
        record = UserSocialAuth.objects.get(
            user=self.user, provider=self.PROVIDER_BACKEND, uid__startswith=self.PROVIDER_IDP_SLUG
        )
        attributes = record.extra_data["attributes"]
        self.assertEqual(
            attributes.get("urn:oid:1.3.6.1.4.1.5923.1.1.1.9"), ["Member@testshib.org", "Staff@testshib.org"]
        )
        self.assertEqual(attributes.get("urn:oid:2.5.4.3"), ["Me Myself And I"])
        self.assertEqual(attributes.get("urn:oid:0.9.2342.19200300.100.1.1"), ["myself"])
        self.assertEqual(attributes.get("urn:oid:2.5.4.20"), ["555-5555"])  # Phone number

    @ddt.data(True, False)
    def test_debug_mode_login(self, debug_mode_enabled):
        """ Test SAML login logs with debug mode enabled or not """
        self._configure_testshib_provider(debug_mode=debug_mode_enabled)
        with patch.object(saml_log, 'info') as mock_log:
            super(TestShibIntegrationTest, self).test_login()
        if debug_mode_enabled:
            # We expect that test_login() does two full logins, and each attempt generates two
            # logs - one for the request and one for the response
            self.assertEqual(mock_log.call_count, 4)

            (msg, action_type, idp_name, xml), _kwargs = mock_log.call_args_list[0]
            self.assertTrue(msg.startswith("SAML login %s"))
            self.assertEqual(action_type, "request")
            self.assertEqual(idp_name, self.PROVIDER_IDP_SLUG)
            self.assertIn('<samlp:AuthnRequest', xml)

            (msg, action_type, idp_name, xml), _kwargs = mock_log.call_args_list[1]
            self.assertTrue(msg.startswith("SAML login %s"))
            self.assertEqual(action_type, "response")
            self.assertEqual(idp_name, self.PROVIDER_IDP_SLUG)
            self.assertIn('<saml2p:Response', xml)
        else:
            self.assertFalse(mock_log.called)

    def test_configure_testshib_provider_with_cache_duration(self):
        """ Enable and configure the TestShib SAML IdP as a third_party_auth provider """
        kwargs = {}
        kwargs.setdefault('name', self.PROVIDER_NAME)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('visible', True)
        kwargs.setdefault('idp_slug', self.PROVIDER_IDP_SLUG)
        kwargs.setdefault('entity_id', TESTSHIB_ENTITY_ID)
        kwargs.setdefault('metadata_source', TESTSHIB_METADATA_URL_WITH_CACHE_DURATION)
        kwargs.setdefault('icon_class', 'fa-university')
        kwargs.setdefault('attr_email', 'urn:oid:1.3.6.1.4.1.5923.1.1.1.6')  # eduPersonPrincipalName
        self.configure_saml_provider(**kwargs)
        self.assertTrue(httpretty.is_enabled())
        num_changed, num_failed, num_total = fetch_saml_metadata()
        self.assertEqual(num_failed, 0)
        self.assertEqual(num_changed, 1)
        self.assertEqual(num_total, 1)

    def _freeze_time(self, timestamp):
        """ Mock the current time for SAML, so we can replay canned requests/responses """
        now_patch = patch('onelogin.saml2.utils.OneLogin_Saml2_Utils.now', return_value=timestamp)
        now_patch.start()
        self.addCleanup(now_patch.stop)

    def _configure_testshib_provider(self, **kwargs):
        """ Enable and configure the TestShib SAML IdP as a third_party_auth provider """
        fetch_metadata = kwargs.pop('fetch_metadata', True)
        kwargs.setdefault('name', self.PROVIDER_NAME)
        kwargs.setdefault('enabled', True)
        kwargs.setdefault('visible', True)
        kwargs.setdefault('idp_slug', self.PROVIDER_IDP_SLUG)
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

    def do_provider_login(self, provider_redirect_url):
        """ Mocked: the user logs in to TestShib and then gets redirected back """
        # The SAML provider (TestShib) will authenticate the user, then get the browser to POST a response:
        self.assertTrue(provider_redirect_url.startswith(TESTSHIB_SSO_URL))
        return self.client.post(
            self.complete_url,
            content_type='application/x-www-form-urlencoded',
            data=self.read_data_file('testshib_response.txt'),
        )
