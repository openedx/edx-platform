"""
Third_party_auth integration tests using a mock version of the TestShib provider
"""

import json
import unittest
import httpretty
from mock import patch

from django.core.urlresolvers import reverse

from student.tests.factories import UserFactory
from third_party_auth.tasks import fetch_saml_metadata
from third_party_auth.tests import testutil
from openedx.core.lib.js_utils import escape_json_dumps


TESTSHIB_ENTITY_ID = 'https://idp.testshib.org/idp/shibboleth'
TESTSHIB_METADATA_URL = 'https://mock.testshib.org/metadata/testshib-providers.xml'
TESTSHIB_SSO_URL = 'https://idp.testshib.org/idp/profile/SAML2/Redirect/SSO'

TPA_TESTSHIB_LOGIN_URL = '/auth/login/tpa-saml/?auth_entry=login&next=%2Fdashboard&idp=testshib'
TPA_TESTSHIB_REGISTER_URL = '/auth/login/tpa-saml/?auth_entry=register&next=%2Fdashboard&idp=testshib'
TPA_TESTSHIB_COMPLETE_URL = '/auth/complete/tpa-saml/'


@unittest.skipUnless(testutil.AUTH_FEATURE_ENABLED, 'third_party_auth not enabled')
class TestShibIntegrationTest(testutil.SAMLTestCase):
    """
    TestShib provider Integration Test, to test SAML functionality
    """
    def setUp(self):
        super(TestShibIntegrationTest, self).setUp()
        self.login_page_url = reverse('signin_user')
        self.register_page_url = reverse('register_user')
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

    def test_login_before_metadata_fetched(self):
        self._configure_testshib_provider(fetch_metadata=False)
        # The user goes to the login page, and sees a button to login with TestShib:
        self._check_login_page()
        # The user clicks on the TestShib button:
        try_login_response = self.client.get(TPA_TESTSHIB_LOGIN_URL)
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
        self.assertIn('"currentProvider": "TestShib"', register_response.content)
        self.assertIn('"errorMessage": null', register_response.content)
        # Now do a crude check that the data (e.g. email) from the provider is displayed in the form:
        self.assertIn('"defaultValue": "myself@testshib.org"', register_response.content)
        self.assertIn('"defaultValue": "Me Myself And I"', register_response.content)
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
        self.assertEqual(continue_response['Location'], self.url_prefix + reverse('dashboard'))

        # Now check that we can login again:
        self.client.logout()
        self.verify_user_email('myself@testshib.org')
        self._test_return_login()

    def test_login(self):
        self._configure_testshib_provider()
        self._freeze_time(timestamp=1434326820)  # This is the time when the saved request/response was recorded.
        user = UserFactory.create()
        # The user goes to the login page, and sees a button to login with TestShib:
        self._check_login_page()
        # The user clicks on the TestShib button:
        try_login_response = self.client.get(TPA_TESTSHIB_LOGIN_URL)
        # The user should be redirected to TestShib:
        self.assertEqual(try_login_response.status_code, 302)
        self.assertTrue(try_login_response['Location'].startswith(TESTSHIB_SSO_URL))
        # Now the user will authenticate with the SAML provider
        testshib_response = self._fake_testshib_login_and_return()
        # We should be redirected to the login screen since this account is not linked to an edX account:
        self.assertEqual(testshib_response.status_code, 302)
        self.assertEqual(testshib_response['Location'], self.url_prefix + self.login_page_url)
        login_response = self.client.get(self.login_page_url)
        # We'd now like to see if the "You've successfully signed into TestShib" message is
        # shown, but it's managed by a JavaScript runtime template, and we can't run JS in this
        # type of test, so we just check for the variable that triggers that message.
        self.assertIn('"currentProvider": "TestShib"', login_response.content)
        self.assertIn('"errorMessage": null', login_response.content)
        # Now the user enters their username and password.
        # The AJAX on the page will log them in:
        ajax_login_response = self.client.post(
            reverse('user_api_login_session'),
            {'email': user.email, 'password': 'test'}
        )
        self.assertEqual(ajax_login_response.status_code, 200)
        # Then the AJAX will finish the third party auth:
        continue_response = self.client.get(TPA_TESTSHIB_COMPLETE_URL)
        # And we should be redirected to the dashboard:
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(continue_response['Location'], self.url_prefix + reverse('dashboard'))

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

    def _check_login_page(self):
        """ Load the login form and check that it contains a TestShib button """
        response = self.client.get(self.login_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("TestShib", response.content)
        self.assertIn(escape_json_dumps(TPA_TESTSHIB_LOGIN_URL), response.content)
        return response

    def _check_register_page(self):
        """ Load the login form and check that it contains a TestShib button """
        response = self.client.get(self.register_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("TestShib", response.content)
        self.assertIn(escape_json_dumps(TPA_TESTSHIB_REGISTER_URL), response.content)
        return response

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
