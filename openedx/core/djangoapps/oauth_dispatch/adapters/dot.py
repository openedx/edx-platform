"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from oauth2_provider import models

from openedx.core.djangoapps.oauth_dispatch.models import RestrictedApplication


class DOTAdapter:
    """
    Standard interface for working with django-oauth-toolkit
    """

    backend = object()
    FILTER_USER_ME = 'user:me'

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

    def create_access_token_for_test(self, token_string, client, user, expires):
        """
        Returns a new AccessToken object created from the given arguments.
        This method is currently used only by tests.
        """
        return models.AccessToken.objects.create(
            token=token_string,
            application=client,
            user=user,
            expires=expires,
        )

    def get_token_scope_names(self, token):
        """
        Given an access token object, return its scopes.
        """
        return list(token.scopes)

    def is_client_restricted(self, client):
        """
        Returns true if the client is set up as a RestrictedApplication.
        """
        return RestrictedApplication.objects.filter(application=client).exists()

    def get_authorization_filters(self, client):
        """
        Get the authorization filters for the given client application.
        """
        application = client

        filter_set = set()
        if hasattr(application, 'access') and application.access.filters:
            filter_set.update(application.access.filters)

        # Allow applications configured with the client credentials grant type to access
        # data for all users. This will enable these applications to fetch data in bulk.
        # Applications configured with all other grant types should only have access
        # to data for the request user.
        if application.authorization_grant_type != application.GRANT_CLIENT_CREDENTIALS:
            filter_set.add(self.FILTER_USER_ME)

        return list(filter_set)
