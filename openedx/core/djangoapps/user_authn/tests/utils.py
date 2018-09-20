""" Common utilities for tests in the user_authn app. """
from django.conf import settings
from openedx.core.djangoapps.oauth_dispatch.adapters.dot import DOTAdapter
from student.tests.factories import UserFactory


def setup_login_oauth_client():
    """
    Sets up a test OAuth client for the login service.
    """
    login_service_user = UserFactory.create()
    DOTAdapter().create_public_client(
        name='login-service',
        user=login_service_user,
        redirect_uri='',
        client_id=settings.JWT_AUTH['JWT_LOGIN_CLIENT_ID'],
    )
