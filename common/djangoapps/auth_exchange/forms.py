"""
Forms to support third-party to first-party OAuth 2.0 access token exchange
"""
from django.contrib.auth.models import User
from django.forms import CharField
from oauth2_provider.constants import SCOPE_NAMES
import provider.constants
from provider.forms import OAuthForm, OAuthValidationError
from provider.oauth2.forms import ScopeChoiceField, ScopeMixin
from provider.oauth2.models import Client
from requests import HTTPError
from social.backends import oauth as social_oauth
from social.exceptions import AuthException

from third_party_auth import pipeline


class AccessTokenExchangeForm(ScopeMixin, OAuthForm):
    """Form for access token exchange endpoint"""
    access_token = CharField(required=False)
    scope = ScopeChoiceField(choices=SCOPE_NAMES, required=False)
    client_id = CharField(required=False)

    def __init__(self, request, *args, **kwargs):
        super(AccessTokenExchangeForm, self).__init__(*args, **kwargs)
        self.request = request

    def _require_oauth_field(self, field_name):
        """
        Raise an appropriate OAuthValidationError error if the field is missing
        """
        field_val = self.cleaned_data.get(field_name)
        if not field_val:
            raise OAuthValidationError(
                {
                    "error": "invalid_request",
                    "error_description": "{} is required".format(field_name),
                }
            )
        return field_val

    def clean_access_token(self):
        """
        Validates and returns the "access_token" field.
        """
        return self._require_oauth_field("access_token")

    def clean_client_id(self):
        """
        Validates and returns the "client_id" field.
        """
        return self._require_oauth_field("client_id")

    def clean(self):
        if self._errors:
            return {}

        backend = self.request.backend
        if not isinstance(backend, social_oauth.BaseOAuth2):
            raise OAuthValidationError(
                {
                    "error": "invalid_request",
                    "error_description": "{} is not a supported provider".format(backend.name),
                }
            )

        self.request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_LOGIN_API

        client_id = self.cleaned_data["client_id"]
        try:
            client = Client.objects.get(client_id=client_id)
        except Client.DoesNotExist:
            raise OAuthValidationError(
                {
                    "error": "invalid_client",
                    "error_description": "{} is not a valid client_id".format(client_id),
                }
            )
        if client.client_type != provider.constants.PUBLIC:
            raise OAuthValidationError(
                {
                    # invalid_client isn't really the right code, but this mirrors
                    # https://github.com/edx/django-oauth2-provider/blob/edx/provider/oauth2/forms.py#L331
                    "error": "invalid_client",
                    "error_description": "{} is not a public client".format(client_id),
                }
            )
        self.cleaned_data["client"] = client

        user = None
        try:
            user = backend.do_auth(self.cleaned_data.get("access_token"), allow_inactive_user=True)
        except (HTTPError, AuthException):
            pass
        if user and isinstance(user, User):
            self.cleaned_data["user"] = user
        else:
            # Ensure user does not re-enter the pipeline
            self.request.social_strategy.clean_partial_pipeline()
            raise OAuthValidationError(
                {
                    "error": "invalid_grant",
                    "error_description": "access_token is not valid",
                }
            )

        return self.cleaned_data
