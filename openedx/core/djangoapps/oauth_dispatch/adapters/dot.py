"""
Adapter to isolate django-oauth-toolkit dependencies
"""

from oauth2_provider import models

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
