"""
Test configurations for lms
"""
from datetime import datetime, timedelta

import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory


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


@pytest.fixture(name='courses')
def course_overviews(current_time):
    """
    Fixture which returns multiple courses
    """
    course_start_end_date = {
        'start_date': current_time - timedelta(days=1),
        'end_date': current_time + timedelta(days=1),
    }
    return {
        'test_course1': CourseOverviewFactory(language='en', **course_start_end_date),
        'test_course2': CourseOverviewFactory(language='ar', **course_start_end_date),
    }
