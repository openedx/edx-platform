"""
Test utilities for OAuth access token exchange
"""
import json

import httpretty
import provider.constants
from provider.oauth2.models import Client
from social.apps.django_app.default.models import UserSocialAuth

from student.tests.factories import UserFactory


class AccessTokenExchangeTestMixin(object):
    """
    A mixin to define test cases for access token exchange. The following
    methods must be implemented by subclasses:
    * _assert_error(data, expected_error, expected_error_description)
    * _assert_success(data, expected_scopes)
    """
    def setUp(self):
        super(AccessTokenExchangeTestMixin, self).setUp()

        self.client_id = "test_client_id"
        self.oauth_client = Client.objects.create(
            client_id=self.client_id,
            client_type=provider.constants.PUBLIC
        )
        self.social_uid = "test_social_uid"
        self.user = UserFactory()
        UserSocialAuth.objects.create(user=self.user, provider=self.BACKEND, uid=self.social_uid)
        self.access_token = "test_access_token"
        # Initialize to minimal data
        self.data = {
            "access_token": self.access_token,
            "client_id": self.client_id,
        }

    def _setup_provider_response(self, success):
        """
        Register a mock response for the third party user information endpoint;
        success indicates whether the response status code should be 200 or 400
        """
        if success:
            status = 200
            body = json.dumps({self.UID_FIELD: self.social_uid})
        else:
            status = 400
            body = json.dumps({})
        httpretty.register_uri(
            httpretty.GET,
            self.USER_URL,
            body=body,
            status=status,
            content_type="application/json"
        )

    def _assert_error(self, _data, _expected_error, _expected_error_description):
        """
        Given request data, execute a test and check that the expected error
        was returned (along with any other appropriate assertions).
        """
        raise NotImplementedError()

    def _assert_success(self, data, expected_scopes):
        """
        Given request data, execute a test and check that the expected scopes
        were returned (along with any other appropriate assertions).
        """
        raise NotImplementedError()

    def test_minimal(self):
        self._setup_provider_response(success=True)
        self._assert_success(self.data, expected_scopes=[])

    def test_scopes(self):
        self._setup_provider_response(success=True)
        self.data["scope"] = "profile email"
        self._assert_success(self.data, expected_scopes=["profile", "email"])

    def test_missing_fields(self):
        for field in ["access_token", "client_id"]:
            data = dict(self.data)
            del data[field]
            self._assert_error(data, "invalid_request", "{} is required".format(field))

    def test_invalid_client(self):
        self.data["client_id"] = "nonexistent_client"
        self._assert_error(
            self.data,
            "invalid_client",
            "nonexistent_client is not a valid client_id"
        )

    def test_confidential_client(self):
        self.oauth_client.client_type = provider.constants.CONFIDENTIAL
        self.oauth_client.save()
        self._assert_error(
            self.data,
            "invalid_client",
            "test_client_id is not a public client"
        )

    def test_invalid_acess_token(self):
        self._setup_provider_response(success=False)
        self._assert_error(self.data, "invalid_grant", "access_token is not valid")

    def test_no_linked_user(self):
        UserSocialAuth.objects.all().delete()
        self._setup_provider_response(success=True)
        self._assert_error(self.data, "invalid_grant", "access_token is not valid")


class AccessTokenExchangeMixinFacebook(object):
    """Tests access token exchange with the Facebook backend"""
    BACKEND = "facebook"
    USER_URL = "https://graph.facebook.com/me"
    # In facebook responses, the "id" field is used as the user's identifier
    UID_FIELD = "id"


class AccessTokenExchangeMixinGoogle(object):
    """Tests access token exchange with the Google backend"""
    BACKEND = "google-oauth2"
    USER_URL = "https://www.googleapis.com/oauth2/v1/userinfo"
    # In google-oauth2 responses, the "email" field is used as the user's identifier
    UID_FIELD = "email"
