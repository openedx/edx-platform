"""
Helpers for tests that require user authentication.
"""
from django.apps import apps
from django.conf import settings
from django.test import TestCase


class UserAuthnTestCase(TestCase):
    """
    Test cases that require user authentication.
    """
    @classmethod
    def setUpClass(cls):
        super(UserAuthnTestCase, cls).setUpClass()
#        cls._add_login_service()

    @classmethod
    def _add_login_service(cls):
        """
        Adds a user and DOT application for the login service.

        NOTE: This code was copied from the migration: 0001_data__add_login_service.py
        """
        login_service_name = 'Login Service for JWT Cookies'
        login_service_client_id = settings.JWT_AUTH['JWT_LOGIN_CLIENT_ID']
        login_service_username = settings.JWT_AUTH['JWT_LOGIN_SERVICE_USERNAME']
        login_service_email = login_service_username + '@fake.email'

        Application = apps.get_model(settings.OAUTH2_PROVIDER_APPLICATION_MODEL)
        if Application.objects.filter(client_id=login_service_client_id).exists():
            return

        # Get the User model using the AUTH_USER_MODEL settings since that is
        # what the Application model expects at this time in the migration phase.
        User = apps.get_model(settings.AUTH_USER_MODEL)
        login_service_user, created = User.objects.get_or_create(
            username=login_service_username,
            email=login_service_email,
        )
        if created:
            # Make sure the login service user's password is unusable.
            # The set_unusable_password method is available on the other User model.
            from django.contrib.auth.models import User
            user = User.objects.get(username=login_service_username)
            user.set_unusable_password()
            user.save()

        login_service_app = Application.objects.create(
            name=login_service_name,
            client_id=login_service_client_id,
            user=login_service_user,
            client_type='public',
            authorization_grant_type='password',
            redirect_uris='',
        )
