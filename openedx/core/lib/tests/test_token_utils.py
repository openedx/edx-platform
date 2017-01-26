"""Tests covering utilities for working with ID tokens."""
import calendar
import datetime

import ddt
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.test.utils import override_settings
import freezegun
import jwt
from nose.plugins.attrib import attr
from edx_oauth2_provider.tests.factories import ClientFactory
from provider.constants import CONFIDENTIAL

from openedx.core.lib.token_utils import get_id_token
from student.models import anonymous_id_for_user
from student.tests.factories import UserFactory, UserProfileFactory


@attr('shard_2')
@ddt.ddt
class TestIdTokenGeneration(TestCase):
    """Tests covering ID token generation."""
    client_name = 'edx-dummy-client'

    def setUp(self):
        super(TestIdTokenGeneration, self).setUp()

        self.oauth2_client = ClientFactory(name=self.client_name, client_type=CONFIDENTIAL)

        self.user = UserFactory.build()
        self.user.save()

    @override_settings(OAUTH_OIDC_ISSUER='test-issuer', OAUTH_ID_TOKEN_EXPIRATION=1)
    @freezegun.freeze_time('2015-01-01 12:00:00')
    @ddt.data(True, False)
    def test_get_id_token(self, has_profile):
        """Verify that ID tokens are signed with the correct secret and generated with the correct claims."""
        full_name = UserProfileFactory(user=self.user).name if has_profile else None

        token = get_id_token(self.user, self.client_name)

        payload = jwt.decode(
            token,
            self.oauth2_client.client_secret,
            audience=self.oauth2_client.client_id,
            issuer=settings.OAUTH_OIDC_ISSUER,
        )

        now = datetime.datetime.utcnow()
        expiration = now + datetime.timedelta(seconds=settings.OAUTH_ID_TOKEN_EXPIRATION)

        expected_payload = {
            'preferred_username': self.user.username,
            'name': full_name,
            'email': self.user.email,
            'administrator': self.user.is_staff,
            'iss': settings.OAUTH_OIDC_ISSUER,
            'exp': calendar.timegm(expiration.utctimetuple()),
            'iat': calendar.timegm(now.utctimetuple()),
            'aud': self.oauth2_client.client_id,
            'sub': anonymous_id_for_user(self.user, None),
        }

        self.assertEqual(payload, expected_payload)

    def test_get_id_token_invalid_client(self):
        """Verify that ImproperlyConfigured is raised when an invalid client name is provided."""
        with self.assertRaises(ImproperlyConfigured):
            get_id_token(self.user, 'does-not-exist')
