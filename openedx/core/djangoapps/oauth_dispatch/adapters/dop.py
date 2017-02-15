"""
Adapter to isolate django-oauth2-provider dependencies
"""

from provider.oauth2 import models
from provider import constants, scope


class DOPAdapter(object):
    """
    Standard interface for working with django-oauth2-provider
    """

    backend = object()

    def create_confidential_client(self, name, user, redirect_uri, client_id=None):
        """
        Create an oauth client application that is confidential.
        """
        return models.Client.objects.create(
            name=name,
            user=user,
            client_id=client_id,
            redirect_uri=redirect_uri,
            client_type=constants.CONFIDENTIAL,
        )

    def create_public_client(self, name, user, redirect_uri, client_id=None):
        """
        Create an oauth client application that is public.
        """
        return models.Client.objects.create(
            name=name,
            user=user,
            client_id=client_id,
            redirect_uri=redirect_uri,
            client_type=constants.PUBLIC,
        )

    def get_client(self, **filters):
        """
        Get the oauth client application with the specified filters.

        Wraps django's queryset.get() method.
        """
        return models.Client.objects.get(**filters)

    def get_client_for_token(self, token):
        """
        Given an AccessToken object, return the associated client application.
        """
        return token.client

    def get_access_token(self, token_string):
        """
        Given a token string, return the matching AccessToken object.
        """
        return models.AccessToken.objects.get(token=token_string)

    def normalize_scopes(self, scopes):
        """
        Given a list of scopes, return a space-separated list of those scopes.
        """
        return ' '.join(scopes)

    def get_token_scope_names(self, token):
        """
        Given an access token object, return its scopes.
        """
        return scope.to_names(token.scope)
