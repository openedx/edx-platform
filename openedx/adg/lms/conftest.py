"""
Test configurations for lms
"""
from datetime import datetime

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


@pytest.fixture(scope='function', name='get_course')
def course_fixture():
    """
    Creates a function to create a course with the given values in kwargs

    Returns:
        func: A function that allows user to create a course with the specified kwargs
    """

    def create_course(**kwargs):
        """
        Create a course overview object from the given keyword args if provided

        Arguments:
            kwargs: Any values to create the course with

        Returns:
             CourseOverview: A course overview object with the provided values
        """
        return CourseOverviewFactory(**kwargs)

    return create_course
