"""
Logistration API View Tests
"""
import ddt
from django.conf import settings
from django.urls import reverse
from mock import patch
from rest_framework.test import APITestCase
from six.moves.urllib.parse import urlencode

from openedx.core.djangolib.testing.utils import skip_unless_lms
from common.djangoapps.third_party_auth import pipeline
from common.djangoapps.third_party_auth.tests.testutil import ThirdPartyAuthTestMixin, simulate_running_pipeline


@skip_unless_lms
@ddt.ddt
class TPAContextViewTest(ThirdPartyAuthTestMixin, APITestCase):
    """
    Third party auth context tests
    """

    def setUp(self):  # pylint: disable=arguments-differ
        """
        Test Setup
        """
        super(TPAContextViewTest, self).setUp()

        self.url = reverse('third_party_auth_context')
        self.query_params = {'redirect_to': '/dashboard'}

        # Several third party auth providers are created for these tests:
        self.configure_google_provider(enabled=True, visible=True)
        self.configure_facebook_provider(enabled=True, visible=True)

        self.hidden_enabled_provider = self.configure_linkedin_provider(
            visible=False,
            enabled=True,
        )

    def _third_party_login_url(self, backend_name, auth_entry, params):
        """
        Construct the login URL to start third party authentication
        """
        return u'{url}?auth_entry={auth_entry}&{param_str}'.format(
            url=reverse('social:begin', kwargs={'backend': backend_name}),
            auth_entry=auth_entry,
            param_str=urlencode(params)
        )

    def get_provider_data(self, params):
        """
        Returns the expected provider data based on providers enabled in test setup
        """
        return [
            {
                'id': 'oa2-facebook',
                'name': 'Facebook',
                'iconClass': 'fa-facebook',
                'iconImage': None,
                'loginUrl': self._third_party_login_url('facebook', 'login', params),
                'registerUrl': self._third_party_login_url('facebook', 'register', params)
            },
            {
                'id': 'oa2-google-oauth2',
                'name': 'Google',
                'iconClass': 'fa-google-plus',
                'iconImage': None,
                'loginUrl': self._third_party_login_url('google-oauth2', 'login', params),
                'registerUrl': self._third_party_login_url('google-oauth2', 'register', params)
            },
        ]

    def get_context(self, params=None, current_provider=None, backend_name=None, add_user_details=False):
        """
        Returns the third party auth context
        """
        return {
            'currentProvider': current_provider,
            'providers': self.get_provider_data(params) if params else [],
            'secondaryProviders': [],
            'finishAuthUrl': pipeline.get_complete_url(backend_name) if backend_name else None,
            'errorMessage': None,
            'registerFormSubmitButtonText': 'Create Account',
            'syncLearnerProfileData': False,
            'pipeline_user_details': {'email': 'test@test.com'} if add_user_details else {}
        }

    def test_missing_arguments(self):
        """
        Test that if required arguments are missing, proper status code and message
        is returned.
        """
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {'message': 'Request missing required parameter: redirect_to'})

    @patch.dict(settings.FEATURES, {'ENABLE_THIRD_PARTY_AUTH': False})
    def test_no_third_party_auth_providers(self):
        """
        Test that if third party auth is enabled, context returned by API contains
        the provider information
        """
        response = self.client.get(self.url, self.query_params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_context())

    def test_third_party_auth_providers(self):
        """
        Test that api returns details of currently enabled third party auth providers
        """
        response = self.client.get(self.url, self.query_params)
        params = {
            'next': self.query_params['redirect_to']
        }

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_context(params))

    @ddt.data(
        ('google-oauth2', 'Google', False),
        ('facebook', 'Facebook', False),
        ('google-oauth2', 'Google', True)
    )
    @ddt.unpack
    def test_running_pipeline(self, current_backend, current_provider, add_user_details):
        """
        Test that when third party pipeline is running, the api returns details
        of current provider
        """
        email = 'test@test.com' if add_user_details else None
        params = {
            'next': self.query_params['redirect_to']
        }

        # Simulate a running pipeline
        pipeline_target = 'openedx.core.djangoapps.user_authn.views.login_form.third_party_auth.pipeline'
        with simulate_running_pipeline(pipeline_target, current_backend, email=email):
            response = self.client.get(self.url, self.query_params)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, self.get_context(params, current_provider, current_backend, add_user_details))

    def test_tpa_hint(self):
        """
        Test that if tpa_hint is provided, the context returns the third party auth provider
        even if it is not visible on the login page
        """
        params = {
            'next': self.query_params['redirect_to']
        }
        tpa_hint = self.hidden_enabled_provider.provider_id
        self.query_params.update({'tpa_hint': tpa_hint})

        provider_data = self.get_provider_data(params)
        provider_data.append({
            'id': self.hidden_enabled_provider.provider_id,
            'name': 'LinkedIn',
            'iconClass': 'fa-linkedin',
            'iconImage': None,
            'loginUrl': self._third_party_login_url('linkedin-oauth2', 'login', params),
            'registerUrl': self._third_party_login_url('linkedin-oauth2', 'register', params)
        })

        response = self.client.get(self.url, self.query_params)
        self.assertEqual(response.data['providers'], provider_data)
