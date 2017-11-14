# pylint: disable=missing-docstring

from datetime import datetime, timedelta

import factory
import pytz
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText
from oauth2_provider.models import AbstractApplication, AccessToken, RefreshToken, get_application_model

from openedx.core.djangoapps.oauth_dispatch.models import Application
from student.tests.factories import UserFactory


class ApplicationFactory(DjangoModelFactory):
    class Meta(object):
        model = get_application_model()

    user = factory.SubFactory(UserFactory)
    client_type = AbstractApplication.CLIENT_CONFIDENTIAL
    authorization_grant_type = AbstractApplication.GRANT_AUTHORIZATION_CODE


class AccessTokenFactory(DjangoModelFactory):
    class Meta(object):
        model = AccessToken
        django_get_or_create = ('user', 'application')

    token = FuzzyText(length=32)
    expires = datetime.now(pytz.UTC) + timedelta(days=1)


class RefreshTokenFactory(DjangoModelFactory):
    class Meta(object):
        model = RefreshToken
        django_get_or_create = ('user', 'application')

    token = FuzzyText(length=32)
