"""
Classes that override default django-oauth-toolkit behavior
"""
from __future__ import unicode_literals

from datetime import datetime

from django.contrib.auth import authenticate, get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from oauth2_provider.models import AccessToken
from oauth2_provider.oauth2_validators import OAuth2Validator
from oauth2_provider.scopes import get_scopes_backend
from pytz import utc

from ..models import RestrictedApplication


@receiver(pre_save, sender=AccessToken)
def on_access_token_presave(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument
    """
    Mark AccessTokens as expired for 'restricted applications' if required.
    """
    if RestrictedApplication.should_expire_access_token(instance.application):
        instance.expires = datetime(1970, 1, 1, tzinfo=utc)


class EdxOAuth2Validator(OAuth2Validator):
    """
    Validator class that implements edX-specific custom behavior:

        * It allows users to log in with their email or username.
        * It does not require users to be active before logging in.
    """

    def validate_user(self, username, password, client, request, *args, **kwargs):
        """
        Authenticate users, but allow inactive users (with u.is_active == False)
        to authenticate.
        """
        user = self._authenticate(username=username, password=password)
        if user is not None:
            request.user = user
            return True
        return False

    def _authenticate(self, username, password):
        """
        Authenticate the user, allowing the user to identify themselves either
        by username or email
        """

        authenticated_user = authenticate(username=username, password=password)
        if authenticated_user is None:
            UserModel = get_user_model()  # pylint: disable=invalid-name
            try:
                email_user = UserModel.objects.get(email=username)
            except UserModel.DoesNotExist:
                authenticated_user = None
            else:
                authenticated_user = authenticate(username=email_user.username, password=password)
        return authenticated_user

    def save_bearer_token(self, token, request, *args, **kwargs):
        """
        Ensure that access tokens issued via client credentials grant are
        associated with the owner of the ``Application``.

        Also, update the `expires_in` value in the token response for
        RestrictedApplications.
        """
        grant_type = request.grant_type
        user = request.user

        if grant_type == 'client_credentials':
            # Temporarily remove the grant type to avoid triggering the super method's code that removes request.user.
            request.grant_type = None

            # Ensure the tokens get associated with the correct user since DOT does not normally
            # associate access tokens issued with the client_credentials grant to users.
            request.user = request.client.user

        super(EdxOAuth2Validator, self).save_bearer_token(token, request, *args, **kwargs)

        if RestrictedApplication.should_expire_access_token(request.client):
            # Since RestrictedApplications will override the DOT defined expiry, so that access_tokens
            # are always expired, we need to re-read the token from the database and then calculate the
            # expires_in (in seconds) from what we stored in the database. This value should be a negative
            #value, meaning that it is already expired

            access_token = AccessToken.objects.get(token=token['access_token'])
            utc_now = datetime.utcnow().replace(tzinfo=utc)
            expires_in = (access_token.expires - utc_now).total_seconds()

            # assert that RestrictedApplications only issue expired tokens
            # blow up processing if we see otherwise
            assert expires_in < 0

            token['expires_in'] = expires_in

        # Restore the original request attributes
        request.grant_type = grant_type
        request.user = user

    def validate_scopes(self, client_id, scopes, client, request, *args, **kwargs):
        """
        Ensure required scopes are permitted (as specified in the settings file)
        """
        available_scopes = get_scopes_backend().get_available_scopes(application=client, request=request)
        return set(scopes).issubset(set(available_scopes))
