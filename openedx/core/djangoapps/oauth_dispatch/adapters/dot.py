"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from django.conf import settings
from oauth2_provider import models
from oauth2_provider.settings import oauth2_settings
from oauthlib.oauth2.rfc6749.tokens import BearerToken

from openedx.core.djangoapps.oauth_dispatch.models import RestrictedApplication


class DOTAdapter(object):
    """
    Standard interface for working with django-oauth-toolkit
    """

    backend = object()
    FILTER_USER_ME = u'user:me'

    def create_confidential_client(self,
                                   name,
                                   user,
                                   redirect_uri,
                                   client_id=None,
                                   authorization_grant_type=models.Application.GRANT_AUTHORIZATION_CODE):
        """
        Create an oauth client application that is confidential.
        """
        return models.Application.objects.create(
            name=name,
            user=user,
            client_id=client_id,
            client_type=models.Application.CLIENT_CONFIDENTIAL,
            authorization_grant_type=authorization_grant_type,
            redirect_uris=redirect_uri,
        )

    def create_public_client(self, name, user, redirect_uri, client_id=None,
                             grant_type=models.Application.GRANT_PASSWORD):
        """
        Create an oauth client application that is public.
        """
        return models.Application.objects.create(
            name=name,
            user=user,
            client_id=client_id,
            client_type=models.Application.CLIENT_PUBLIC,
            authorization_grant_type=grant_type,
            redirect_uris=redirect_uri,
        )

    def get_client(self, **filters):
        """
        Get the oauth client application with the specified filters.

        Wraps django's queryset.get() method.
        """
        return models.Application.objects.get(**filters)

    def get_client_for_token(self, token):
        """
        Given an AccessToken object, return the associated client application.
        """
        return token.application

    def get_access_token(self, token_string):
        """
        Given a token string, return the matching AccessToken object.
        """
        return models.AccessToken.objects.get(token=token_string)

    def normalize_scopes(self, scopes):
        """
        Given a list of scopes, return a space-separated list of those scopes.
        """
        if not scopes:
            scopes = ['default']
        return ' '.join(scopes)

    def get_token_scope_names(self, token):
        """
        Given an access token object, return its scopes.
        """
        return list(token.scopes)

    def is_client_restricted(self, client_id):
        """
        Returns true if the client is set up as a RestrictedApplication.
        """
        application = self.get_client(client_id=client_id)
        return RestrictedApplication.objects.filter(application=application).exists()

    def get_authorization_filters(self, client_id):
        """
        Get the authorization filters for the given client application.
        """
        application = self.get_client(client_id=client_id)
        filters = [org_relation.to_jwt_filter_claim() for org_relation in application.organizations.all()]

        # Allow applications configured with the client credentials grant type to access
        # data for all users. This will enable these applications to fetch data in bulk.
        # Applications configured with all other grant types should only have access
        # to data for the request user.
        if application.authorization_grant_type != application.GRANT_CLIENT_CREDENTIALS:
            filters.append(self.FILTER_USER_ME)

        return filters

    def create_access_token(self, request, user, scope, client, refresh_token=None):
        """
        Create and return a new access token.
        """
        _days = 24 * 60 * 60
        token_generator = BearerToken(
            expires_in=settings.OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS * _days,
            request_validator=oauth2_settings.OAUTH2_VALIDATOR_CLASS(),
        )
        self._populate_create_access_token_request(request, user, scope, client, refresh_token)
        return token_generator.create_token(request, refresh_token=True)

    def _populate_create_access_token_request(self, request, user, scope, client, refresh_token=None):
        """
        django-oauth-toolkit expects certain non-standard attributes to
        be present on the request object.  This function modifies the
        request object to match these expectations
        """
        request.user = user
        request.scopes = ['default']
        request.client = client
        request.state = None
        request.refresh_token = refresh_token
        request.extra_credentials = None
        request.grant_type = client.authorization_grant_type
