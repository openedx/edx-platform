from unittest import skipIf, skipUnless

from django.conf import settings
from django.contrib.auth.models import User
from django.db import connection
from django.db.utils import IntegrityError
from django.test import TestCase


@skipIf(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This test ensures backward-compatible behaviour')
class SingleTenantEmailsModelTest(TestCase):
    """
    Ensure the default Open edX behaviour is maintained while the APPSEMBLER_MULTI_TENANT_EMAILS feature is turned off.
    """

    def test_installed_apps(self):
        assert 'openedx.core.djangoapps.appsembler.multi_tenant_emails' not in settings.INSTALLED_APPS

    @skipIf(connection.vendor == 'sqlite', 'Needs MySQL to run django_fixups migrations')
    def test_duplicate_email_prevent(self):
        """
        Test to ensure duplicate email isn't allowed by default in Open edX.

        Appsembler: During tests the UNIQUE constraint for emails is never added for SQLite as of
                    Django 1.11 in so this test won't work for SQLite.

                    The database-level unique constraint by `django_fixups` work only in production
                    environments for MySQL and possibly Postgres.

                    We're keeping this as a reminder not to spend time on this issue.
        """
        email = 'same-email@example.com'
        User.objects.create(username='user_site1', email=email)

        with self.assertRaises(IntegrityError):
            User.objects.create(username='user_site2', email=email)


@skipUnless(settings.FEATURES['APPSEMBLER_MULTI_TENANT_EMAILS'], 'This tests multi-tenancy')
class MultiTenantEmailsModelTest(TestCase):
    """
    Test when the APPSEMBLER_MULTI_TENANT_EMAILS feature is turned on.
    """
    def test_installed_apps(self):
        assert 'openedx.core.djangoapps.appsembler.multi_tenant_emails' in settings.INSTALLED_APPS

    def test_duplicate_email_allow(self):
        email = 'same-email@example.com'
        User.objects.create(username='user_site1', email=email)
        User.objects.create(username='user_site2', email=email)
