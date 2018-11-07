"""
Contains tests for OAuth2 model-retirement methods.
"""

import datetime

from django.test import TestCase
from openedx.core.djangoapps.oauth_dispatch.tests import factories
from student.tests.factories import UserFactory
from oauth2_provider.models import (
    AccessToken as DOTAccessToken,
    Application as DOTApplication,
    RefreshToken as DOTRefreshToken,
    Grant as DOTGrant,
)
from provider.oauth2.models import (
    AccessToken as DOPAccessToken,
    RefreshToken as DOPRefreshToken,
    Grant as DOPGrant,
    Client as DOPClient,
)

from ..oauth2_retirement_utils import (
    retire_dop_oauth2_models,
    retire_dot_oauth2_models,
)


class RetireDOTModelsTest(TestCase):

    def test_delete_dot_models(self):
        user = UserFactory.create()
        app = factories.ApplicationFactory(user=user)
        access_token = factories.AccessTokenFactory(
            user=user,
            application=app
        )
        factories.RefreshTokenFactory(
            user=user,
            application=app,
            access_token=access_token,
        )
        DOTGrant.objects.create(
            user=user,
            application=app,
            expires=datetime.datetime(2018, 1, 1),
        )

        retire_dot_oauth2_models(user)

        applications = DOTApplication.objects.filter(user_id=user.id)
        access_tokens = DOTAccessToken.objects.filter(user_id=user.id)
        refresh_tokens = DOTRefreshToken.objects.filter(user_id=user.id)
        grants = DOTGrant.objects.filter(user=user)

        query_sets = [applications, access_tokens, refresh_tokens, grants]

        for query_set in query_sets:
            self.assertFalse(query_set.exists())


class RetireDOPModelsTest(TestCase):

    def test_delete_dop_models(self):
        user = UserFactory.create()
        client = DOPClient.objects.create(
            user=user,
            client_type=1,
        )
        access_token = DOPAccessToken.objects.create(
            user=user,
            client=client,
        )
        DOPRefreshToken.objects.create(
            user=user,
            client=client,
            access_token=access_token,
        )

        retire_dop_oauth2_models(user)

        access_tokens = DOPAccessToken.objects.filter(user=user)
        refresh_tokens = DOPRefreshToken.objects.filter(user=user)
        grants = DOPGrant.objects.filter(user_id=user.id)

        query_sets = [access_tokens, refresh_tokens, grants]

        for query_set in query_sets:
            self.assertFalse(query_set.exists())
