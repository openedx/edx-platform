"""
Classes that override default django-oauth-toolkit behavior
"""
from __future__ import unicode_literals

from datetime import datetime

import django
from django.contrib.auth import authenticate, get_user_model
from django.db.models.signals import pre_save
from django.dispatch import receiver
from oauth2_provider.models import AccessToken
from oauth2_provider.oauth2_validators import OAuth2Validator
from pytz import utc
from ratelimitbackend.backends import RateLimitMixin

from ..models import RestrictedApplication


@receiver(pre_save, sender=AccessToken)
def on_access_token_presave(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument
    """
    A hook on the AccessToken. Since we do not have protected scopes, we must mark all
    AccessTokens as expired for 'restricted applications'.

    We do this as a pre-save hook on the ORM
    """

    is_application_restricted = RestrictedApplication.objects.filter(application=instance.application).exists()
    if is_application_restricted:
        RestrictedApplication.set_access_token_as_expired(instance)


# TODO: Remove Django 1.11 upgrade shim
# SHIM: Allow users that are inactive to still authenticate while keeping rate-limiting functionality.
if django.VERSION < (1, 10):
    # Old backend which allowed inactive users to authenticate prior to Django 1.10.
    from django.contrib.auth.backends import ModelBackend as UserModelBackend
else:
    # Django 1.10+ ModelBackend disallows inactive users from authenticating, so instead we use
    # AllowAllUsersModelBackend which is the closest alternative.
    from django.contrib.auth.backends import AllowAllUsersModelBackend as UserModelBackend


class EdxRateLimitedAllowAllUsersModelBackend(RateLimitMixin, UserModelBackend):
    """
    Authentication backend needed to incorporate rate limiting of login attempts - but also
    enabling users with is_active of False in the Django auth_user model to still authenticate.
    This is necessary for mobile users using 3rd party auth who have not activated their accounts,
    Inactive users who use 1st party auth (username/password auth) will still fail login attempts,
    just at a higher layer, in the login_user view.

    See: https://openedx.atlassian.net/browse/TNL-4516
    """
    pass


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

        is_application_restricted = RestrictedApplication.objects.filter(application=request.client).exists()
        if is_application_restricted:
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
