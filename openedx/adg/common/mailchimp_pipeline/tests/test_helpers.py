"""
All tests for mailchimp pipeline helpers
"""
from datetime import datetime

import pytest

from openedx.adg.common.course_meta.tests.factories import CourseMetaFactory
from openedx.adg.common.mailchimp_pipeline.helpers import get_enrollment_course_names_and_short_ids_by_user
from student.tests.factories import CourseEnrollmentFactory, UserFactory


@pytest.fixture
def user_enrollments():
    """
    A fixture for enrolling user into multiple running courses.
    """
    user = UserFactory()
    enrollment_data = {'user': user, 'is_active': True, 'course__end_date': datetime(2022, 1, 1)}
    enrollment1 = CourseEnrollmentFactory(course__display_name='course1', **enrollment_data)
    enrollment2 = CourseEnrollmentFactory(course__display_name='course2', **enrollment_data)
    enrollment3 = CourseEnrollmentFactory(course__display_name='course3', **enrollment_data)
    enrolled_courses = [enrollment1.course, enrollment2.course, enrollment3.course]

    for course in enrolled_courses:
        CourseMetaFactory(course=course)

    return user, enrolled_courses


@pytest.mark.django_db
def test_get_enrollment_course_names_and_short_ids_by_user(user_enrollments):  # pylint: disable=redefined-outer-name
    """
    Assert that all active and running enrolled courses for a user are returned.
    """
    user, _ = user_enrollments
    course_short_ids, course_titles = get_enrollment_course_names_and_short_ids_by_user(user)

    assert course_short_ids == '100, 101, 102'
    assert course_titles == 'course1, course2, course3'
