"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from oauth2_provider import models


class DOTAdapter(object):
    """
    Standard interface for working with django-oauth-toolkit
    """

    backend = object()

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

    def create_public_client(self, name, user, redirect_uri, client_id=None):
        """
        Create an oauth client application that is public.
        """
        return models.Application.objects.create(
            name=name,
            user=user,
            client_id=client_id,
            client_type=models.Application.CLIENT_PUBLIC,
            authorization_grant_type=models.Application.GRANT_PASSWORD,
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
