"""
Tests for IdP-initiated SSO view.
"""

import unittest
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlparse

import ddt
from django.http import Http404, HttpResponseBadRequest
from django.test import RequestFactory
from django.urls import reverse

from common.djangoapps.third_party_auth import pipeline
from common.djangoapps.third_party_auth.idp_initiated_sso import IdpInitiatedSsoView
from common.djangoapps.third_party_auth.tests.testutil import AUTH_FEATURE_ENABLED, AUTH_FEATURES_KEY, SAMLTestCase


@unittest.skipUnless(AUTH_FEATURE_ENABLED, AUTH_FEATURES_KEY + ' not enabled')
@ddt.ddt
class IdpInitiatedSsoViewTest(SAMLTestCase):
    """
    Test the IdpInitiatedSsoView for Auth0 IdP-initiated SSO.
    """

    def setUp(self):
        super().setUp()
        self.view = IdpInitiatedSsoView.as_view()
        self.factory = RequestFactory()
        self.endpoint_url = reverse('idp_initiated_sso_login')

    def _create_oauth_provider(self, provider_id='test-oauth', backend_name='oauth2', enabled=True):
        """Helper to create a mock OAuth2 provider."""
        from common.djangoapps.third_party_auth import provider as provider_module
        
        # Create a mock provider
        mock_provider = Mock()
        mock_provider.provider_id = provider_id
        mock_provider.backend_name = backend_name
        mock_provider.enabled = enabled
        
        return mock_provider

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    def test_valid_connection_redirects_to_provider(self, mock_get_login_url, mock_registry_enabled):
        """Test that a valid connection parameter redirects to the provider with connection param."""
        # Setup
        mock_provider = self._create_oauth_provider(backend_name='oauth2')
        mock_registry_enabled.return_value = [mock_provider]
        mock_get_login_url.return_value = 'http://example.com/auth/login/oauth2/?auth_entry=login&next=/dashboard'
        
        # Make request
        request = self.factory.get(self.endpoint_url, {'connection': 'my-saml-connection'})
        response = self.view(request)
        
        # Assertions
        assert response.status_code == 302
        redirect_url = response.url
        
        # Verify connection parameter was added
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        assert 'connection' in query_params
        assert query_params['connection'][0] == 'my-saml-connection'
        
        # Verify get_login_url was called
        mock_get_login_url.assert_called_once()

    def test_missing_connection_returns_400(self):
        """Test that missing connection parameter returns 400 error."""
        request = self.factory.get(self.endpoint_url)
        response = self.view(request)
        
        assert isinstance(response, HttpResponseBadRequest)
        assert b'Missing required "connection" parameter' in response.content

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    def test_no_oauth_provider_returns_404(self, mock_registry_enabled):
        """Test that when no OAuth provider exists, returns 404."""
        # Setup - return a SAML provider instead of OAuth
        mock_saml_provider = Mock()
        mock_saml_provider.backend_name = 'tpa-saml'
        mock_registry_enabled.return_value = [mock_saml_provider]
        
        # Make request
        request = self.factory.get(self.endpoint_url, {'connection': 'my-connection'})
        
        # Should raise 404
        with self.assertRaises(Http404) as context:
            self.view(request)
        
        assert 'No suitable OAuth/OIDC provider found' in str(context.exception)

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    def test_next_url_preserved(self, mock_get_login_url, mock_registry_enabled):
        """Test that the next parameter is preserved through the flow."""
        # Setup
        mock_provider = self._create_oauth_provider(backend_name='oauth2')
        mock_registry_enabled.return_value = [mock_provider]
        mock_get_login_url.return_value = 'http://example.com/auth/login/oauth2/'
        
        # Make request with next parameter
        request = self.factory.get(
            self.endpoint_url,
            {'connection': 'my-connection', 'next': '/courses/my-course'}
        )
        response = self.view(request)
        
        # Verify get_login_url was called with the next URL
        call_args = mock_get_login_url.call_args
        assert call_args[0][0] == 'test-oauth'  # provider_id
        assert call_args[0][1] == pipeline.AUTH_ENTRY_LOGIN
        assert call_args[1]['redirect_url'] == '/courses/my-course'

    @patch('common.djangoapps.third_party_auth.provider.Registry.get')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    def test_specific_provider_id(self, mock_get_login_url, mock_registry_get):
        """Test that a specific provider_id can be requested."""
        # Setup
        mock_provider = self._create_oauth_provider(provider_id='specific-oauth')
        mock_registry_get.return_value = mock_provider
        mock_get_login_url.return_value = 'http://example.com/auth/login/oauth2/'
        
        # Make request with provider_id
        request = self.factory.get(
            self.endpoint_url,
            {'connection': 'my-connection', 'provider_id': 'specific-oauth'}
        )
        response = self.view(request)
        
        # Verify the specific provider was used
        mock_registry_get.assert_called_once_with('specific-oauth')
        assert response.status_code == 302

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    def test_connection_parameter_added_to_url(self, mock_get_login_url, mock_registry_enabled):
        """Test that the connection parameter is properly added to the redirect URL."""
        # Setup
        mock_provider = self._create_oauth_provider(backend_name='auth0')
        mock_registry_enabled.return_value = [mock_provider]
        
        # Base URL with existing parameters
        base_url = 'http://example.com/auth/login?auth_entry=login&next=/dashboard'
        mock_get_login_url.return_value = base_url
        
        # Make request
        connection_name = 'enterprise-saml-idp'
        request = self.factory.get(self.endpoint_url, {'connection': connection_name})
        response = self.view(request)
        
        # Parse redirect URL
        redirect_url = response.url
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        
        # Verify all parameters are present
        assert 'auth_entry' in query_params
        assert 'next' in query_params
        assert 'connection' in query_params
        assert query_params['connection'][0] == connection_name

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    @ddt.data(
        'oauth2',
        'oidc',
        'auth0',
        'custom-oauth2-provider',
    )
    def test_oauth_backend_detection(self, backend_name, mock_get_login_url, mock_registry_enabled):
        """Test that various OAuth backend names are correctly detected."""
        # Setup
        mock_provider = self._create_oauth_provider(backend_name=backend_name)
        mock_registry_enabled.return_value = [mock_provider]
        mock_get_login_url.return_value = 'http://example.com/auth/login/'
        
        # Make request
        request = self.factory.get(self.endpoint_url, {'connection': 'test'})
        response = self.view(request)
        
        # Should successfully redirect
        assert response.status_code == 302

    @patch('common.djangoapps.third_party_auth.provider.Registry.enabled')
    @patch('common.djangoapps.third_party_auth.pipeline.get_login_url')
    def test_get_login_url_error_handling(self, mock_get_login_url, mock_registry_enabled):
        """Test that errors from get_login_url are properly handled."""
        # Setup
        mock_provider = self._create_oauth_provider(backend_name='oauth2')
        mock_registry_enabled.return_value = [mock_provider]
        mock_get_login_url.side_effect = ValueError('Provider not enabled')
        
        # Make request
        request = self.factory.get(self.endpoint_url, {'connection': 'test'})
        
        # Should raise 404
        with self.assertRaises(Http404) as context:
            self.view(request)
        
        assert 'Failed to generate login URL' in str(context.exception)
