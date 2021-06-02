"""
Test configurations for lms
"""
from datetime import datetime

import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory


@pytest.fixture(name='current_time')
def current_datetime():
    return datetime.now()


@pytest.fixture(name='user_with_profile')
def user_with_user_profile(request):
    """
    Create user with profile, this fixture will be passed as a parameter to all pytests
    """
    user = UserFactory()
    UserProfileFactory(user=user)
    return user


@pytest.fixture(name='user_client')
def user_client_login(request, client):
    """
    User and client login fixture. User will be authenticated for all tests where we pass this fixture.
    """
    user = UserFactory()
    client.login(username=user.username, password='test')
    return user, client
