"""
Forms to support third-party to first-party OAuth 2.0 access token exchange
"""
import logging

import provider.constants
from django.contrib.auth.models import User
from django.forms import CharField
from edx_oauth2_provider.constants import SCOPE_NAMES
from oauth2_provider.models import Application
from provider.forms import OAuthForm, OAuthValidationError
from provider.oauth2.forms import ScopeChoiceField, ScopeMixin
from provider.oauth2.models import Client
from requests import HTTPError
from social_core.backends import oauth as social_oauth
from social_core.exceptions import AuthException

from third_party_auth import pipeline

log = logging.getLogger(__name__)

class AccessTokenExchangeForm(ScopeMixin, OAuthForm):
    """Form for access token exchange endpoint"""
    access_token = CharField(required=False)
    scope = ScopeChoiceField(choices=SCOPE_NAMES, required=False)
    client_id = CharField(required=False)

    def __init__(self, request, oauth2_adapter, *args, **kwargs):
        super(AccessTokenExchangeForm, self).__init__(*args, **kwargs)
        self.request = request
        self.oauth2_adapter = oauth2_adapter

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
            log.info("inside clean 1st if: self._error: [ %s ]", self._errors)
            return {}

        backend = self.request.backend
        log.info("inside clean: backend: [ %s ]", backend)
        if not isinstance(backend, social_oauth.BaseOAuth2):
            log.info("inside clean: 2nd if: social_oauth.BaseOAuth2 [ %s ], backend.name: [ %s ]",
                     social_oauth.BaseOAuth2, backend.name)
            raise OAuthValidationError(
                {
                    "error": "invalid_request",
                    "error_description": "{} is not a supported provider".format(backend.name),
                }
            )

        self.request.session[pipeline.AUTH_ENTRY_KEY] = pipeline.AUTH_ENTRY_LOGIN_API
        log.info("inside clean: AUTH_ENTRY_KEY [ %s ]", self.request.session[pipeline.AUTH_ENTRY_KEY])
        client_id = self.cleaned_data["client_id"]
        try:
            client = self.oauth2_adapter.get_client(client_id=client_id)
            log.info("inside clean: 1st try block: client: [ %s ], client_id [ %s ]", client, client_id )
        except (Client.DoesNotExist, Application.DoesNotExist):
            raise OAuthValidationError(
                {
                    "error": "invalid_client",
                    "error_description": "{} is not a valid client_id".format(client_id),
                }
            )
        if client.client_type not in [provider.constants.PUBLIC, Application.CLIENT_PUBLIC]:
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
        access_token = self.cleaned_data.get("access_token")
        try:
            user = backend.do_auth(access_token, allow_inactive_user=True)
            log.info("inside clean: 2nd try block: user: [ %s ]", user)
        except (HTTPError, AuthException):
            log.info("inside clean: exception passed")
            pass
        if user and isinstance(user, User):
            self.cleaned_data["user"] = user
            log.info("inside clean last if: user and isinstance(user,User): [ %s ] ", user, isinstance(user, User))
        else:
            # Ensure user does not re-enter the pipeline
            self.request.social_strategy.clean_partial_pipeline(access_token)
            log.info("inside clean: last line exception")
            raise OAuthValidationError(
                {
                    "error": "invalid_grant",
                    "error_description": "access_token is not valid",
                }
            )
        log.info("inside clean: self.cleaned_data: [ %s ]", self.cleaned_data)
        return self.cleaned_data
