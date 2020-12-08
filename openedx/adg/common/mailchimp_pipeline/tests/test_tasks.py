"""
All tests for mailchimp pipeline tasks
"""
import pytest

from openedx.adg.common.mailchimp_pipeline import tasks as mailchimp_tasks
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from student.tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_info_to_mailchimp(mocker):
    """
    Assert that mailchimp client is called with valid data when User is created.
    """
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member

    user = UserFactory()
    user_email = user.email
    user_json = {
        'email_address': user_email,
        'status_if_new': 'subscribed',
        'merge_fields': {
            'DATEREGIS': str(user.date_joined.strftime('%m/%d/%Y')),
            'USERNAME': user.username
        },
    }

    mailchimp_tasks.task_send_user_info_to_mailchimp(user_email, user_json)
    mock_create_or_update_list_member.assert_called_once_with(email=user_email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_enrollments_to_mailchimp(mocker):
    """
    Assert that mailchimp client is called with valid data for syncing user enrollment (and un-enrolment)
    """
    mock_get_or_create = mocker.patch.object(mailchimp_tasks.CourseMeta.objects, 'get_or_create')
    mock_enrolls = mocker.patch.object(mailchimp_tasks, 'get_enrollment_course_names_and_short_ids_by_user')
    mock_enrolls.return_value = '100, 101, 102', 'course1, course2, course3'
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member
    user = UserFactory()
    course = CourseOverviewFactory()

    mailchimp_tasks.task_send_user_enrollments_to_mailchimp(user.id, course.id)

    user_json = {
        "email_address": user.email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": 'course1, course2, course3',
            "ENROLL_IDS": '100, 101, 102',
        }
    }

    mock_get_or_create.assert_called_once_with(course=course)
    mock_create_or_update_list_member.assert_called_once_with(email=user.email, data=user_json)


@pytest.mark.django_db
@pytest.mark.mute_signals
def test_task_send_user_enrollments_to_mailchimp_invalid_course_id(mocker):
    """
    Assert that mailchimp client is not called due to invalid course id
    """
    mock_log_error = mocker.patch.object(mailchimp_tasks.log, 'error')
    mock_get_or_create = mocker.patch.object(mailchimp_tasks.CourseMeta.objects, 'get_or_create')

    mailchimp_tasks.task_send_user_enrollments_to_mailchimp(UserFactory().id, 'course/test/123')

    mock_log_error.assert_called_once_with(mocker.ANY)
    assert not mock_get_or_create.called
