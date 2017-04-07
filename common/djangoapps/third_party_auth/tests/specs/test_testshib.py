"""
Third_party_auth integration tests using a mock version of the TestShib provider
"""
import ddt
import unittest
import httpretty
import json
from mock import patch
from social.apps.django_app.default.models import UserSocialAuth
from unittest import skip

from third_party_auth.saml import log as saml_log
from third_party_auth.tasks import fetch_saml_metadata
from third_party_auth.tests import testutil

from .base import IntegrationTestMixin


TESTSHIB_ENTITY_ID = 'https://idp.testshib.org/idp/shibboleth'
TESTSHIB_METADATA_URL = 'https://mock.testshib.org/metadata/testshib-providers.xml'
TESTSHIB_METADATA_URL_WITH_CACHE_DURATION = 'https://mock.testshib.org/metadata/testshib-providers-cache.xml'
TESTSHIB_SSO_URL = 'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO'


class SamlIntegrationTestUtilities(object):
    """
    Class contains methods particular to SAML integration testing so that they
    can be separated out from the actual test methods.
    """
    PROVIDER_ID = "saml-testshib"
    PROVIDER_NAME = "TestShib"
    PROVIDER_BACKEND = "tpa-saml"
    PROVIDER_IDP_SLUG = "testshib"

    USER_EMAIL = "myself@testshib.org"
    USER_NAME = "Me Myself And I"
    USER_USERNAME = "myself"

    def setUp(self):
        super(SamlIntegrationTestUtilities, self).setUp()
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

    def _freeze_time(self, timestamp):
        """ Mock the current time for SAML, so we can replay canned requests/responses """
        now_patch = patch('onelogin.saml2.utils.OneLogin_Saml2_Utils.now', return_value=timestamp)
        now_patch.start()
        self.addCleanup(now_patch.stop)

    def _configure_testshib_provider(self, **kwargs):
        """ Enable and configure the TestShib SAML IdP as a third_party_auth provider """
        fetch_metadata = kwargs.pop('fetch_metadata', True)
        assert_metadata_updates = kwargs.pop('assert_metadata_updates', True)
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
            num_total, num_skipped, num_attempted, num_updated, num_failed, failure_messages = fetch_saml_metadata()
            if assert_metadata_updates:
                self.assertEqual(num_total, 1)
                self.assertEqual(num_skipped, 0)
                self.assertEqual(num_attempted, 1)
                self.assertEqual(num_updated, 1)
                self.assertEqual(num_failed, 0)
                self.assertEqual(len(failure_messages), 0)

    def do_provider_login(self, provider_redirect_url):
        """ Mocked: the user logs in to TestShib and then gets redirected back """
        # The SAML provider (TestShib) will authenticate the user, then get the browser to POST a response:
        self.assertTrue(provider_redirect_url.startswith(TESTSHIB_SSO_URL))
        return self.client.post(
            self.complete_url,
            content_type='application/x-www-form-urlencoded',
            data=self.read_data_file('testshib_response.txt'),
        )


@ddt.ddt
@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestShibIntegrationTest(SamlIntegrationTestUtilities, IntegrationTestMixin, testutil.SAMLTestCase):
    """
    TestShib provider Integration Test, to test SAML functionality
    """

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
        num_total, num_skipped, num_attempted, num_updated, num_failed, failure_messages = fetch_saml_metadata()
        self.assertEqual(num_total, 1)
        self.assertEqual(num_skipped, 0)
        self.assertEqual(num_attempted, 1)
        self.assertEqual(num_updated, 1)
        self.assertEqual(num_failed, 0)
        self.assertEqual(len(failure_messages), 0)


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class SuccessFactorsIntegrationTest(SamlIntegrationTestUtilities, IntegrationTestMixin, testutil.SAMLTestCase):
    """
    Test basic SAML capability using the TestShib details, and then check that we're able
    to make the proper calls using the SAP SuccessFactors API.
    """

    # Note that these details are different than those that will be provided by the SAML
    # assertion metadata. Rather, they will be fetched from the mocked SAPSuccessFactors API.
    USER_EMAIL = "john@smith.com"
    USER_NAME = "John Smith"
    USER_USERNAME = "jsmith"

    def setUp(self):
        """
        Mock out HTTP calls to various endpoints using httpretty.
        """
        super(SuccessFactorsIntegrationTest, self).setUp()

        # Mock the call to the SAP SuccessFactors assertion endpoint
        SAPSF_ASSERTION_URL = 'http://successfactors.com/oauth/idp'

        def assertion_callback(_request, _uri, headers):
            """
            Return a fake assertion after checking that the input is what we expect.
            """
            self.assertIn('private_key=fake_private_key_here', _request.body)
            self.assertIn('user_id=myself', _request.body)
            self.assertIn('token_url=http%3A%2F%2Fsuccessfactors.com%2Foauth%2Ftoken', _request.body)
            self.assertIn('client_id=TatVotSEiCMteSNWtSOnLanCtBGwNhGB', _request.body)
            return (200, headers, 'fake_saml_assertion')

        httpretty.register_uri(httpretty.POST, SAPSF_ASSERTION_URL, content_type='text/plain', body=assertion_callback)

        SAPSF_BAD_ASSERTION_URL = 'http://successfactors.com/oauth-fake/idp'

        def bad_callback(_request, _uri, headers):
            """
            Return a 404 error when someone tries to call the URL.
            """
            return (404, headers, 'NOT AN ASSERTION')

        httpretty.register_uri(httpretty.POST, SAPSF_BAD_ASSERTION_URL, content_type='text/plain', body=bad_callback)

        # Mock the call to the SAP SuccessFactors token endpoint
        SAPSF_TOKEN_URL = 'http://successfactors.com/oauth/token'

        def token_callback(_request, _uri, headers):
            """
            Return a fake assertion after checking that the input is what we expect.
            """
            self.assertIn('assertion=fake_saml_assertion', _request.body)
            self.assertIn('company_id=NCC1701D', _request.body)
            self.assertIn('grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Asaml2-bearer', _request.body)
            self.assertIn('client_id=TatVotSEiCMteSNWtSOnLanCtBGwNhGB', _request.body)
            return (200, headers, '{"access_token": "faketoken"}')

        httpretty.register_uri(httpretty.POST, SAPSF_TOKEN_URL, content_type='application/json', body=token_callback)

        # Mock the call to the SAP SuccessFactors OData user endpoint
        ODATA_USER_URL = (
            'http://api.successfactors.com/odata/v2/User(userId=\'myself\')'
            '?$select=username,firstName,lastName,defaultFullName,email'
        )

        def user_callback(request, _uri, headers):
            auth_header = request.headers.get('Authorization')
            self.assertEqual(auth_header, 'Bearer faketoken')
            return (
                200,
                headers,
                json.dumps({
                    'd': {
                        'username': 'jsmith',
                        'firstName': 'John',
                        'lastName': 'Smith',
                        'defaultFullName': 'John Smith',
                        'email': 'john@smith.com',
                    }
                })
            )

        httpretty.register_uri(httpretty.GET, ODATA_USER_URL, content_type='application/json', body=user_callback)

    def test_register_insufficient_sapsf_metadata(self):
        """
        Configure the provider such that it doesn't have enough details to contact the SAP
        SuccessFactors API, and test that it falls back to the data it receives from the SAML assertion.
        """
        self._configure_testshib_provider(
            identity_provider_type='sap_success_factors',
            metadata_source=TESTSHIB_METADATA_URL,
            other_settings='{"key_i_dont_need":"value_i_also_dont_need"}',
        )
        # Because we're getting details from the assertion, fall back to the initial set of details.
        self.USER_EMAIL = "myself@testshib.org"
        self.USER_NAME = "Me Myself And I"
        self.USER_USERNAME = "myself"
        super(SuccessFactorsIntegrationTest, self).test_register()

    def test_register_sapsf_metadata_present(self):
        """
        Configure the provider such that it can talk to a mocked-out version of the SAP SuccessFactors
        API, and ensure that the data it gets that way gets passed to the registration form.
        """
        self._configure_testshib_provider(
            identity_provider_type='sap_success_factors',
            metadata_source=TESTSHIB_METADATA_URL,
            other_settings=json.dumps({
                'sapsf_oauth_root_url': 'http://successfactors.com/oauth/',
                'sapsf_private_key': 'fake_private_key_here',
                'odata_api_root_url': 'http://api.successfactors.com/odata/v2/',
                'odata_company_id': 'NCC1701D',
                'odata_client_id': 'TatVotSEiCMteSNWtSOnLanCtBGwNhGB',
            })
        )
        super(SuccessFactorsIntegrationTest, self).test_register()

    def test_register_http_failure(self):
        """
        Ensure that if there's an HTTP failure while fetching metadata, we continue, using the
        metadata from the SAML assertion.
        """
        self._configure_testshib_provider(
            identity_provider_type='sap_success_factors',
            metadata_source=TESTSHIB_METADATA_URL,
            other_settings=json.dumps({
                'sapsf_oauth_root_url': 'http://successfactors.com/oauth-fake/',
                'sapsf_private_key': 'fake_private_key_here',
                'odata_api_root_url': 'http://api.successfactors.com/odata/v2/',
                'odata_company_id': 'NCC1701D',
                'odata_client_id': 'TatVotSEiCMteSNWtSOnLanCtBGwNhGB',
            })
        )
        # Because we're getting details from the assertion, fall back to the initial set of details.
        self.USER_EMAIL = "myself@testshib.org"
        self.USER_NAME = "Me Myself And I"
        self.USER_USERNAME = "myself"
        super(SuccessFactorsIntegrationTest, self).test_register()

    @skip('Test not necessary for this subclass')
    def test_get_saml_idp_class_with_fake_identifier(self):
        pass

    @skip('Test not necessary for this subclass')
    def test_login(self):
        pass

    @skip('Test not necessary for this subclass')
    def test_register(self):
        pass
