"""Tests covering JWT construction utilities."""
import ddt
from django.test import TestCase
import jwt
from nose.plugins.attrib import attr

from lms.djangoapps.oauth_dispatch.tests import mixins
from openedx.core.lib.token_utils import JwtBuilder
from student.tests.factories import UserFactory, UserProfileFactory


@attr(shard=2)
@ddt.ddt
class TestJwtBuilder(mixins.AccessTokenMixin, TestCase):
    """
    Test class for JwtBuilder.
    """

    expires_in = 10

    def setUp(self):
        super(TestJwtBuilder, self).setUp()

        self.user = UserFactory()
        self.profile = UserProfileFactory(user=self.user)

    @ddt.data(
        [],
        ['email'],
        ['profile'],
        ['email', 'profile'],
    )
    def test_jwt_construction(self, scopes):
        """
        Verify that a valid JWT is built, including claims for the requested scopes.
        """
        token = JwtBuilder(self.user).build_token(scopes, self.expires_in)
        self.assert_valid_jwt_access_token(token, self.user, scopes)

    def test_user_profile_missing(self):
        """
        Verify that token construction succeeds if the UserProfile is missing.
        """
        self.profile.delete()  # pylint: disable=no-member

        scopes = ['profile']
        token = JwtBuilder(self.user).build_token(scopes, self.expires_in)
        self.assert_valid_jwt_access_token(token, self.user, scopes)

    def test_override_secret_and_audience(self):
        """
        Verify that the signing key and audience can be overridden.
        """
        secret = 'avoid-this'
        audience = 'avoid-this-too'
        scopes = []

        token = JwtBuilder(self.user, secret=secret).build_token(scopes, self.expires_in, aud=audience)

        jwt.decode(token, secret, audience=audience)
