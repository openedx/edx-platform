'''
Utilities for contentstore tests
'''

from datetime import timedelta
from django.conf import settings
from django.utils import timezone

from provider.oauth2.models import AccessToken, Client as OAuth2Client
from provider import constants
from rest_framework.test import APIClient

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


def create_oauth2_client(user):
    """
    Create an OAuth2 client associated with the given user and generate an
    access token for said client.

    :param user:
    :return: a Client (provider.oauth2) and an AccessToken
    """
    # Register an OAuth2 Client
    client = OAuth2Client(
        user=user,
        name=user.username,
        url="http://127.0.0.1/",
        redirect_uri="http://127.0.0.1/",
        client_type=constants.CONFIDENTIAL
    )
    client.save()

    # Generate an access token for the client
    access_token = AccessToken(
        user=user,
        client=client,

        # Set the access token to expire one day from now
        expires=timezone.now() + timedelta(1, 0),
        scope=constants.READ_WRITE
    )
    access_token.save()

    return client, access_token


def use_access_token(client, access_token):
    """
    Make an APIClient pass an access token for all requests

    :param client: an APIClient
    :param access_token: an AccessToken
    """
    client.credentials(
        HTTP_AUTHORIZATION="Bearer {}".format(access_token.token)
    )

    return client


class CourseTestCase(ModuleStoreTestCase):
    """
    Extendable base for test cases dealing with courses
    """
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client can
        log them in.
        The test user is created in the ModuleStoreTestCase setUp method.
        They inherit from the ModuleStoreTestCase class so that the mongodb
        collection will be cleared out before each test case execution and
        deleted afterwards.
        """
        self.user_password = super(CourseTestCase, self).setUp()

        # Create an APIClient to simulate requests (like the Django Client, but
        # without CSRF)
        api_client = APIClient()

        # Register an OAuth2 Client
        _oauth2_client, access_token = create_oauth2_client(self.user)
        self.client = use_access_token(api_client, access_token)

        self.course = CourseFactory.create()

    def create_non_staff_authed_user_client(self):
        """
        Create a non-staff user, log them in (if authenticate=True), and return
        the client, user to use for testing.
        """
        nonstaff, _password = self.create_non_staff_user()

        client = APIClient()

        return client, nonstaff
