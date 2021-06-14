"""
Test configurations for lms
"""
from datetime import datetime, timedelta

import pytest
from django.utils import timezone

from common.djangoapps.student.tests.factories import UserFactory, UserProfileFactory
from openedx.adg.lms.applications.tests.constants import BUSINESS_LINE_PRE_REQ
from openedx.adg.lms.applications.tests.factories import MultilingualCourseFactory, MultilingualCourseGroupFactory
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


@pytest.fixture(name='prereq_course_groups')
def create_prerequisite_course_group(request):
    """
    This fixture takes in a tuple to set the batch size of course groups to be created and to make these
    course groups either program or business line prerequisite e.g. (10, 'business_line_pre_req')

    request: a fixture providing information of the requesting test function
    """

    if request.param[1] == BUSINESS_LINE_PRE_REQ:
        course_groups = MultilingualCourseGroupFactory.create_batch(
            request.param[0], is_program_prerequisite=False, is_common_business_line_prerequisite=True
        )
    else:
        course_groups = MultilingualCourseGroupFactory.create_batch(request.param[0])

    for course_group in course_groups:
        now = timezone.now()
        # Open prereq courses
        MultilingualCourseFactory.create_batch(
            2, course__start_date=now, course__end_date=now + timedelta(days=1), multilingual_course_group=course_group
        )
        # Ended prereq course
        MultilingualCourseFactory(
            course__start_date=now - timedelta(days=2), course__end_date=now, multilingual_course_group=course_group
        )

    return course_groups
