"""
View for handling IdP-initiated SSO login flows.

This view supports Auth0's IdP-initiated SAML sign-on to OIDC apps pattern,
where Auth0 acts as a SAML Service Provider and presents an OIDC interface to edX.

Reference: https://auth0.com/docs/authenticate/protocols/saml/saml-sso-integrations/configure-idp-initiated-saml-sign-on-to-oidc-apps
"""

from logging import getLogger
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from django.http import Http404, HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import View

from common.djangoapps.third_party_auth import pipeline, provider
from common.djangoapps.student.helpers import get_next_url_for_login_page

logger = getLogger(__name__)


class IdpInitiatedSsoView(View):
    """
    Handle IdP-initiated SSO login requests.
    
    This view is designed to work with Auth0's IdP-initiated SAML flow where:
    1. Auth0 receives SAML assertion from an external IdP
    2. Auth0 redirects to this endpoint with a 'connection' parameter
    3. This view redirects to Auth0's OAuth/OIDC endpoint with the connection parameter
    4. Auth0 uses the connection to route to the appropriate SAML IdP
    
    Expected query parameters:
        - connection (required): Auth0's SAML connection name
        - next (optional): URL to redirect to after successful authentication
        - provider_id (optional): edX provider ID; if not provided, uses the first enabled OAuth provider
    """
    
    def get(self, request):
        """
        Handle GET request for IdP-initiated SSO login.
        
        Args:
            request: HttpRequest object
            
        Returns:
            HttpResponse: Redirect to the provider's login URL with connection parameter
            
        Raises:
            HttpResponseBadRequest: If connection parameter is missing
            Http404: If no suitable provider is found
        """
        connection = request.GET.get('connection')
        if not connection:
            logger.warning(
                '[IdP-Initiated SSO] Missing required "connection" parameter. '
                'Request: %s',
                request.GET
            )
            return HttpResponseBadRequest('Missing required "connection" parameter')
        
        # Get the next URL or use default
        next_url = request.GET.get('next')
        if not next_url:
            next_url = get_next_url_for_login_page(request)
        
        # Get provider - either specified or first enabled OAuth provider
        provider_id = request.GET.get('provider_id')
        enabled_provider = self._get_provider(provider_id)
        
        if not enabled_provider:
            logger.error(
                '[IdP-Initiated SSO] No suitable OAuth/OIDC provider found. '
                'provider_id: %s, connection: %s',
                provider_id,
                connection
            )
            raise Http404('No suitable OAuth/OIDC provider found for IdP-initiated SSO')
        
        # Get the base login URL
        try:
            login_url = pipeline.get_login_url(
                enabled_provider.provider_id,
                pipeline.AUTH_ENTRY_LOGIN,
                redirect_url=next_url
            )
        except ValueError as exc:
            logger.error(
                '[IdP-Initiated SSO] Failed to get login URL. '
                'provider_id: %s, connection: %s, error: %s',
                enabled_provider.provider_id,
                connection,
                str(exc)
            )
            raise Http404(f'Failed to generate login URL: {exc}') from exc
        
        # Add the connection parameter to the login URL
        # This will be passed through the pipeline and ultimately to Auth0's /authorize endpoint
        login_url_with_connection = self._add_connection_param(login_url, connection)
        
        logger.info(
            '[IdP-Initiated SSO] Redirecting to provider login. '
            'provider: %s, connection: %s, next_url: %s',
            enabled_provider.provider_id,
            connection,
            next_url
        )
        
        return redirect(login_url_with_connection)
    
    def _get_provider(self, provider_id=None):
        """
        Get the OAuth/OIDC provider to use for authentication.
        
        Args:
            provider_id (str, optional): Specific provider ID to use
            
        Returns:
            Provider: The enabled provider, or None if not found
        """
        if provider_id:
            # Get specific provider if requested
            return provider.Registry.get(provider_id)
        
        # Otherwise, find the first enabled OAuth/OIDC provider
        # We prioritize OAuth2 providers as they're the typical use case with Auth0
        for enabled_provider in provider.Registry.enabled():
            backend_name = enabled_provider.backend_name
            # Check if it's an OAuth2 provider (common backend names)
            if any(oauth_type in backend_name.lower() for oauth_type in ['oauth2', 'oidc', 'auth0']):
                return enabled_provider
        
        # If no OAuth provider found, return None (will result in 404)
        return None
    
    def _add_connection_param(self, url, connection):
        """
        Add the connection parameter to the given URL.
        
        Args:
            url (str): Base URL
            connection (str): Connection name to add
            
        Returns:
            str: URL with connection parameter added
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        query_params['connection'] = [connection]
        
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
