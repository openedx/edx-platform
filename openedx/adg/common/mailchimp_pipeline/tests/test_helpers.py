"""
All tests for mailchimp pipeline helpers
"""
from datetime import datetime

import pytest

from openedx.adg.common.course_meta.tests.factories import CourseMetaFactory
from openedx.adg.common.mailchimp_pipeline import helpers as mailchimp_helpers
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
def test_get_active_enrollment_course_overviews_by_user(user_enrollments):  # pylint: disable=redefined-outer-name
    """
    Assert that all active and running enrolled courses for a user are returned.
    """
    user, enrolled_courses = user_enrollments
    expected_courses = mailchimp_helpers.get_active_enrollment_course_overviews_by_user(user)

    assert expected_courses == enrolled_courses


@pytest.mark.django_db
def test_get_active_enrollment_course_names_by_user(mocker, user_enrollments):  # pylint: disable=redefined-outer-name
    """
    Assert that all active and running enrolled courses for a user are returned.
    """
    user, enrolled_courses = user_enrollments
    mock_courses = mocker.patch.object(mailchimp_helpers, 'get_active_enrollment_course_overviews_by_user')
    mock_courses.return_value = enrolled_courses
    expected_course_titles = mailchimp_helpers.get_active_enrollment_course_names_by_user(user)

    assert expected_course_titles == 'course1, course2, course3'


@pytest.mark.django_db
def test_get_active_enrollment_course_short_ids(mocker, user_enrollments):  # pylint: disable=redefined-outer-name
    """
    Assert that all active and running enrolled courses for a user are returned.
    """
    user, enrolled_courses = user_enrollments
    mock_courses = mocker.patch.object(mailchimp_helpers, 'get_active_enrollment_course_overviews_by_user')
    mock_courses.return_value = enrolled_courses
    expected_course_short_ids = mailchimp_helpers.get_active_enrollment_course_short_ids(user)

    assert expected_course_short_ids == '100, 101, 102'


@pytest.mark.django_db
def test_send_user_info_to_mailchimp(mocker):
    """
    Assert that mailchimp client is called with valid data for syncing user's info
    """
    user = UserFactory()
    mock_mailchimp_client = mocker.patch.object(mailchimp_helpers, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member
    mailchimp_helpers.send_user_info_to_mailchimp(user, False)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "FULLNAME": user.get_full_name(),
            "USERNAME": user.username
        }
    }

    mock_create_or_update_list_member.assert_called_once_with(email=user.email, data=user_json)


@pytest.mark.django_db
def test_send_user_enrollments_to_mailchimp(mocker):
    """
    Assert that mailchimp client is called with valid data for syncing user enrollment (and un-enrolment)
    """
    user = UserFactory()

    mocker.patch('openedx.adg.common.mailchimp_pipeline.helpers.CourseMeta.objects.get_or_create')

    mock_enrolls = mocker.patch.object(mailchimp_helpers, 'get_active_enrollment_course_names_by_user')
    mock_enrolls.return_value = 'course1, course2, course3'

    mock_enroll_ids = mocker.patch.object(mailchimp_helpers, 'get_active_enrollment_course_short_ids')
    mock_enroll_ids.return_value = '100, 101, 102'

    mock_mailchimp_client = mocker.patch.object(mailchimp_helpers, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member

    mailchimp_helpers.send_user_enrollments_to_mailchimp(user, None)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": 'course1, course2, course3',
            "ENROLL_IDS": '100, 101, 102',
        }
    }

    mock_create_or_update_list_member.assert_called_once_with(email=user.email, data=user_json)
