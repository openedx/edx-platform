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

    def create_access_token_for_test(self, token_string, client, user, expires):
        """
        Returns a new AccessToken object created from the given arguments.
        This method is currently used only by tests.
        """
        return models.AccessToken.objects.create(
            token=token_string,
            client=client,
            user=user,
            expires=expires,
        )

    def get_token_scope_names(self, token):
        """
        Given an access token object, return its scopes.
        """
        return scope.to_names(token.scope)

    def is_client_restricted(self, client):  # pylint: disable=unused-argument
        """
        Returns true if the client is set up as a RestrictedApplication.
        """
        return False

    def get_authorization_filters(self, client):  # pylint: disable=unused-argument
        """
        Get the authorization filters for the given client application.
        """
        return []
