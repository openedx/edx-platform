"""
All tests for mailchimp pipeline tasks
"""
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.common.mailchimp_pipeline import tasks as mailchimp_tasks
from openedx.adg.constants import MONTH_DAY_YEAR_FORMAT


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
            'DATEREGIS': str(user.date_joined.strftime(MONTH_DAY_YEAR_FORMAT)),
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
    mock_mailchimp_client = mocker.patch.object(mailchimp_tasks, 'MailchimpClient', autospec=True)
    mock_create_or_update_list_member = mock_mailchimp_client().create_or_update_list_member
    user_email = 'test@example.com'
    user_json = {
        "email_address": user_email,
        "status_if_new": "subscribed",
        "merge_fields": {
            "ENROLLS": 'course1,course2,course3',
            "ENROLL_IDS": '100,101,102',
        }
    }

    mailchimp_tasks.task_send_user_enrollments_to_mailchimp(user_email, user_json)
    mock_create_or_update_list_member.assert_called_once_with(email=user_email, data=user_json)
