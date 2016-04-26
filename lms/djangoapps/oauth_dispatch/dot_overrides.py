"""
Classes that override default django-oauth-toolkit behavior
"""

from django.contrib.auth import authenticate, get_user_model
from oauth2_provider.oauth2_validators import OAuth2Validator


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
        Authenticate the user, allowing the user to identify themself either by
        username or email
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
