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
