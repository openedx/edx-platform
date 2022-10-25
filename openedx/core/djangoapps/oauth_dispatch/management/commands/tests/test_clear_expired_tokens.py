"""
Tests the ``edx_clear_expired_tokens`` management command.
"""


import unittest
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db.models import QuerySet
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone
from oauth2_provider.models import AccessToken, RefreshToken
from testfixtures import LogCapture

from openedx.core.djangoapps.oauth_dispatch.tests import factories
from common.djangoapps.student.tests.factories import UserFactory

LOGGER_NAME = 'openedx.core.djangoapps.oauth_dispatch.management.commands.edx_clear_expired_tokens'


def counter(fn):
    """
    Adds a call counter to the given function.
    Source: http://code.activestate.com/recipes/577534-counting-decorator/
    """
    def _counted(*largs, **kargs):
        _counted.invocations += 1
        return fn(*largs, **kargs)

    _counted.invocations = 0
    return _counted


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EdxClearExpiredTokensTests(TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    # patching REFRESH_TOKEN_EXPIRE_SECONDS because override_settings not working.
    @patch('oauth2_provider.settings.oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS', 'xyz')
    def test_invalid_expiration_time(self):
        with LogCapture(LOGGER_NAME) as log:
            with pytest.raises(ImproperlyConfigured):
                call_command('edx_clear_expired_tokens')
                log.check(
                    (
                        LOGGER_NAME,
                        'EXCEPTION',
                        'REFRESH_TOKEN_EXPIRE_SECONDS must be either a timedelta or seconds'
                    )
                )

    @override_settings()
    def test_excluded_application_ids(self):
        settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'] = 3600
        expires = timezone.now() - timedelta(days=1)
        application = factories.ApplicationFactory()
        access_token = factories.AccessTokenFactory(user=application.user, application=application, expires=expires)
        factories.RefreshTokenFactory(user=application.user, application=application, access_token=access_token)
        with LogCapture(LOGGER_NAME) as log:
            call_command('edx_clear_expired_tokens', sleep_time=0, excluded_application_ids=str(application.id))
            log.check(
                (
                    LOGGER_NAME,
                    'INFO',
                    f'Cleaning {0} rows from {RefreshToken.__name__} table'
                ),
                (
                    LOGGER_NAME,
                    'INFO',
                    f'Cleaning {0} rows from {AccessToken.__name__} table',
                ),
                (
                    LOGGER_NAME,
                    'INFO',
                    'Cleaning 0 rows from Grant table',
                )
            )
        assert RefreshToken.objects.filter(application=application).exists()

    @override_settings()
    def test_clear_expired_tokens(self):
        settings.OAUTH2_PROVIDER['REFRESH_TOKEN_EXPIRE_SECONDS'] = 3600
        initial_count = 5
        now = timezone.now()
        expires = now - timedelta(days=1)
        users = UserFactory.create_batch(initial_count)
        for user in users:
            application = factories.ApplicationFactory(user=user)
            factories.AccessTokenFactory(user=user, application=application, expires=expires)
        assert AccessToken.objects.filter(refresh_token__isnull=True, expires__lt=now).count() == initial_count
        original_delete = QuerySet.delete
        QuerySet.delete = counter(QuerySet.delete)
        try:
            call_command('edx_clear_expired_tokens', batch_size=1, sleep_time=0)
            assert not QuerySet.delete.invocations != initial_count  # pylint: disable=no-member
            assert AccessToken.objects.filter(refresh_token__isnull=True, expires__lt=now).count() == 0
        finally:
            QuerySet.delete = original_delete
