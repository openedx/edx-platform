"""
Customized django-oauth2-provider views
"""

from django.conf import settings

import provider.oauth2.views
import provider.oauth2.forms
from provider import scope
from provider.oauth2.views import OAuthError
from provider.oauth2.views import Capture, Redirect  # pylint: disable=unused-import

from oauth2_provider.forms import PasswordGrantForm
from oauth2_provider.models import TrustedClient
from oauth2_provider.backends import PublicPasswordBackend


# pylint: disable=abstract-method
class Authorize(provider.oauth2.views.Authorize):
    """
    edX customized authorization view:
      - Introduces trusted clients, which do not require user consent.
    """
    def get_authorization_form(self, request, client, data, client_data):
        # Check if the client is trusted. If so, bypass user
        # authorization by filling the data in the form.
        trusted = TrustedClient.objects.filter(client=client).exists()
        if trusted:
            scope_names = scope.to_names(client_data['scope'])
            data = {'authorize': [u'Authorize'], 'scope': scope_names}

        form = provider.oauth2.forms.AuthorizationForm(data)
        return form


# pylint: disable=abstract-method
class AccessTokenView(provider.oauth2.views.AccessTokenView):
    """
    edX customized access token view:
      - Allows usage of email as main identifier when requesting a
        password grant.
      - Return username along access token if requested in the scope.
    """

    # add custom authentication provider
    authentication = (provider.oauth2.views.AccessTokenView.authentication +
                      (PublicPasswordBackend, ))

    def get_password_grant(self, _request, data, client):
        # Use customized form to allow use of user email during authentication
        form = PasswordGrantForm(data, client=client)
        if not form.is_valid():
            raise OAuthError(form.errors)
        return form.cleaned_data

    # pylint: disable=super-on-old-class
    def access_token_response_data(self, access_token):
        # Include username along the access token response if requested in the scope.
        response_data = super(AccessTokenView, self).access_token_response_data(access_token)

        if scope.check(settings.OAUTH_USERNAME_SCOPE, access_token.scope):
            response_data.update({'preferred_username': access_token.user.username})

        return response_data
