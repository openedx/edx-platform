"""
All tests for webinar tasks
"""
import pytest

from openedx.adg.lms.webinars.tasks import task_reschedule_webinar_reminders

from .factories import WebinarRegistrationFactory


@pytest.mark.django_db
def test_task_send_mandrill_email_successfully(mocker, webinar):
    """
    Tests if reschedule_webinar_reminders is called properly when the start_time is updated.
    """
    mock_cancel_reminders = mocker.patch('openedx.adg.lms.webinars.tasks.cancel_all_reminders')
    mock_schedule_reminders = mocker.patch('openedx.adg.lms.webinars.tasks.schedule_webinar_reminders')

    WebinarRegistrationFactory(webinar=webinar)

    task_reschedule_webinar_reminders(webinar.to_dict())

    mock_cancel_reminders.assert_called_once()
    mock_schedule_reminders.assert_called_once()
