"""
Integration tests for third_party_auth LTI auth providers
"""


import unittest
from django.conf import settings
from django.contrib.auth.models import User
from django.urls import reverse
from oauthlib.oauth1.rfc5849 import Client, SIGNATURE_TYPE_BODY
from common.djangoapps.third_party_auth.tests import testutil

FORM_ENCODED = 'application/x-www-form-urlencoded'

LTI_CONSUMER_KEY = 'consumer'
LTI_CONSUMER_SECRET = 'secret'
LTI_TPA_LOGIN_URL = '/auth/login/lti/'
LTI_TPA_COMPLETE_URL = '/auth/complete/lti/'
OTHER_LTI_CONSUMER_KEY = 'settings-consumer'
OTHER_LTI_CONSUMER_SECRET = 'secret2'
LTI_USER_ID = 'lti_user_id'
EDX_USER_ID = 'test_user'
EMAIL = 'lti_user@example.com'


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class IntegrationTestLTI(testutil.TestCase):
    """
    Integration tests for third_party_auth LTI auth providers
    """

    def setUp(self):
        super(IntegrationTestLTI, self).setUp()
        self.hostname = 'testserver'
        self.client.defaults['SERVER_NAME'] = self.hostname
        self.url_prefix = 'http://{}'.format(self.hostname)
        self.configure_lti_provider(
            name='Other Tool Consumer 1', enabled=True,
            lti_consumer_key='other1',
            lti_consumer_secret='secret1',
            lti_max_timestamp_age=10,
        )
        self.configure_lti_provider(
            name='LTI Test Tool Consumer', enabled=True,
            lti_consumer_key=LTI_CONSUMER_KEY,
            lti_consumer_secret=LTI_CONSUMER_SECRET,
            lti_max_timestamp_age=10,
        )
        self.configure_lti_provider(
            name='Tool Consumer with Secret in Settings', enabled=True,
            lti_consumer_key=OTHER_LTI_CONSUMER_KEY,
            lti_consumer_secret='',
            lti_max_timestamp_age=10,
        )
        self.lti = Client(
            client_key=LTI_CONSUMER_KEY,
            client_secret=LTI_CONSUMER_SECRET,
            signature_type=SIGNATURE_TYPE_BODY,
        )

    def test_lti_login(self):
        # The user initiates a login from an external site
        (uri, _headers, body) = self.lti.sign(
            uri=self.url_prefix + LTI_TPA_LOGIN_URL, http_method='POST',
            headers={'Content-Type': FORM_ENCODED},
            body={
                'user_id': LTI_USER_ID,
                'custom_tpa_next': '/account/finish_auth/?course_id=my_course_id&enrollment_action=enroll',
            }
        )
        login_response = self.client.post(path=uri, content_type=FORM_ENCODED, data=body)
        # The user should be redirected to the registration form
        self.assertEqual(login_response.status_code, 302)
        self.assertTrue(login_response['Location'].endswith(reverse('signin_user')))
        register_response = self.client.get(login_response['Location'])
        self.assertContains(register_response, '"currentProvider": "LTI Test Tool Consumer"')
        self.assertContains(register_response, '"errorMessage": null')

        # Now complete the form:
        ajax_register_response = self.client.post(
            reverse('user_api_registration'),
            {
                'email': EMAIL,
                'name': 'Myself',
                'username': EDX_USER_ID,
                'honor_code': True,
            }
        )
        self.assertEqual(ajax_register_response.status_code, 200)
        continue_response = self.client.get(self.url_prefix + LTI_TPA_COMPLETE_URL)
        # The user should be redirected to the finish_auth view which will enroll them.
        # FinishAuthView.js reads the URL parameters directly from $.url
        self.assertEqual(continue_response.status_code, 302)
        self.assertEqual(
            continue_response['Location'],
            '/account/finish_auth/?course_id=my_course_id&enrollment_action=enroll'
        )

        # Now check that we can login again
        self.client.logout()
        self.verify_user_email(EMAIL)
        (uri, _headers, body) = self.lti.sign(
            uri=self.url_prefix + LTI_TPA_LOGIN_URL, http_method='POST',
            headers={'Content-Type': FORM_ENCODED},
            body={'user_id': LTI_USER_ID}
        )
        login_2_response = self.client.post(path=uri, content_type=FORM_ENCODED, data=body)
        # The user should be redirected to the dashboard
        self.assertEqual(login_2_response.status_code, 302)
        self.assertEqual(login_2_response['Location'], LTI_TPA_COMPLETE_URL + "?")
        continue_2_response = self.client.get(login_2_response['Location'])
        self.assertEqual(continue_2_response.status_code, 302)
        self.assertTrue(continue_2_response['Location'].endswith(reverse('dashboard')))

        # Check that the user was created correctly
        user = User.objects.get(email=EMAIL)
        self.assertEqual(user.username, EDX_USER_ID)

    def test_reject_initiating_login(self):
        response = self.client.get(self.url_prefix + LTI_TPA_LOGIN_URL)
        self.assertEqual(response.status_code, 405)  # Not Allowed

    def test_reject_bad_login(self):
        login_response = self.client.post(
            path=self.url_prefix + LTI_TPA_LOGIN_URL, content_type=FORM_ENCODED,
            data="invalid=login",
        )
        # The user should be redirected to the login page with an error message
        # (auth_entry defaults to login for this provider)
        self.assertEqual(login_response.status_code, 302)
        self.assertTrue(login_response['Location'].endswith(reverse('signin_user')))
        error_response = self.client.get(login_response['Location'])
        self.assertContains(
            error_response,
            'Authentication failed: LTI parameters could not be validated.',
        )

    def test_can_load_consumer_secret_from_settings(self):
        lti = Client(
            client_key=OTHER_LTI_CONSUMER_KEY,
            client_secret=OTHER_LTI_CONSUMER_SECRET,
            signature_type=SIGNATURE_TYPE_BODY,
        )
        (uri, _headers, body) = lti.sign(
            uri=self.url_prefix + LTI_TPA_LOGIN_URL, http_method='POST',
            headers={'Content-Type': FORM_ENCODED},
            body={
                'user_id': LTI_USER_ID,
                'custom_tpa_next': '/account/finish_auth/?course_id=my_course_id&enrollment_action=enroll',
            }
        )
        with self.settings(SOCIAL_AUTH_LTI_CONSUMER_SECRETS={OTHER_LTI_CONSUMER_KEY: OTHER_LTI_CONSUMER_SECRET}):
            login_response = self.client.post(path=uri, content_type=FORM_ENCODED, data=body)
            # The user should be redirected to the registration form
            self.assertEqual(login_response.status_code, 302)
            self.assertTrue(login_response['Location'].endswith(reverse('signin_user')))
            register_response = self.client.get(login_response['Location'])
            self.assertContains(
                register_response,
                '"currentProvider": "Tool Consumer with Secret in Settings"',
            )
            self.assertContains(register_response, '"errorMessage": null')
