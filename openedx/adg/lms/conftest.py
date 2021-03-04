"""
Test configurations for lms
"""
from datetime import datetime, timedelta

import pytest

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.adg.lms.applications.tests.factories import MultilingualCourseGroupFactory
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


@pytest.fixture(name='courses')
def course_overviews(current_time):
    """
    Fixture which return multiple courses
    """
    course_start_end_date = {
        'start_date': current_time - timedelta(days=1),
        'end_date': current_time + timedelta(days=1),
    }
    course1 = CourseOverviewFactory(
        language='en',
        **course_start_end_date
    )
    course2 = CourseOverviewFactory(
        language='ar',
        **course_start_end_date
    )
    return {
        'test_course1': course1,
        'test_course2': course2,
    }


@pytest.fixture(name='expired_course')
def expired_course_overview(current_time):
    return CourseOverviewFactory(
        language='en',
        start_date=current_time - timedelta(days=2),
        end_date=current_time - timedelta(days=1),
    )


@pytest.fixture(name='course_group')
def multilingual_course_group():
    return MultilingualCourseGroupFactory()
