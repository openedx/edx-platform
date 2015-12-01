"""
Test utilities for OAuth access token exchange
"""
import provider.constants
from social.apps.django_app.default.models import UserSocialAuth

from third_party_auth.tests.utils import ThirdPartyOAuthTestMixin


class AccessTokenExchangeTestMixin(ThirdPartyOAuthTestMixin):
    """
    A mixin to define test cases for access token exchange. The following
    methods must be implemented by subclasses:
    * _assert_error(data, expected_error, expected_error_description)
    * _assert_success(data, expected_scopes)
    """
    def setUp(self):  # pylint: disable=arguments-differ
        super(AccessTokenExchangeTestMixin, self).setUp()

        # Initialize to minimal data
        self.data = {
            "access_token": self.access_token,
            "client_id": self.client_id,
        }

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

    def test_inactive_user(self):
        self.user.is_active = False
        self.user.save()  # pylint: disable=no-member
        self._setup_provider_response(success=True)
        self._assert_success(self.data, expected_scopes=[])

    def test_invalid_acess_token(self):
        self._setup_provider_response(success=False)
        self._assert_error(self.data, "invalid_grant", "access_token is not valid")

    def test_no_linked_user(self):
        UserSocialAuth.objects.all().delete()
        self._setup_provider_response(success=True)
        self._assert_error(self.data, "invalid_grant", "access_token is not valid")

    def test_user_automatically_linked_by_email(self):
        UserSocialAuth.objects.all().delete()
        self._setup_provider_response(success=True, email=self.user.email)
        self._assert_success(self.data, expected_scopes=[])

    def test_inactive_user_not_automatically_linked(self):
        UserSocialAuth.objects.all().delete()
        self._setup_provider_response(success=True, email=self.user.email)
        self.user.is_active = False
        self.user.save()  # pylint: disable=no-member
        self._assert_error(self.data, "invalid_grant", "access_token is not valid")
