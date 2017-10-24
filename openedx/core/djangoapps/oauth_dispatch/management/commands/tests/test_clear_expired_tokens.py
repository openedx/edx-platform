from datetime import timedelta
import unittest

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.db.models import QuerySet
from django.test import TestCase
from django.utils import timezone
from mock import patch
from oauth2_provider.models import AccessToken
from testfixtures import LogCapture

from openedx.core.djangoapps.oauth_dispatch.tests import factories
from student.tests.factories import UserFactory

LOGGER_NAME = 'openedx.core.djangoapps.oauth_dispatch.management.commands.edx_clear_expired_tokens'


def counter(fn):
    """
    Adds a call counter to the given function.
    Source: http://code.activestate.com/recipes/577534-counting-decorator/
    """
    def _counted(*largs, **kargs):
        _counted.invocations += 1
        fn(*largs, **kargs)

    _counted.invocations = 0
    return _counted


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class EdxClearExpiredTokensTests(TestCase):

    @patch('oauth2_provider.settings.oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS', 'xyz')
    def test_invalid_expiration_time(self):
        with LogCapture(LOGGER_NAME) as log:
            with self.assertRaises(ImproperlyConfigured):
                call_command('edx_clear_expired_tokens')
                log.check(
                    (
                        LOGGER_NAME,
                        'EXCEPTION',
                        'REFRESH_TOKEN_EXPIRE_SECONDS must be either a timedelta or seconds'
                    )
                )

    @patch('oauth2_provider.settings.oauth2_settings.REFRESH_TOKEN_EXPIRE_SECONDS', 3600)
    def test_clear_expired_tokens(self):
        initial_count = 5
        now = timezone.now()
        expires = now - timedelta(days=1)
        users = UserFactory.create_batch(initial_count)
        for user in users:
            application = factories.ApplicationFactory(user=user)
            factories.AccessTokenFactory(user=user, application=application, expires=expires)
        self.assertEqual(
            AccessToken.objects.filter(refresh_token__isnull=True, expires__lt=now).count(),
            initial_count
        )
        QuerySet.delete = counter(QuerySet.delete)

        call_command('edx_clear_expired_tokens', batch_size=1, sleep_time=0)
        self.assertEqual(QuerySet.delete.invocations, initial_count)
        self.assertEqual(AccessToken.objects.filter(refresh_token__isnull=True, expires__lt=now).count(), 0)
