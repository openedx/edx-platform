"""
All tests for webinars handler functions
"""
import pytest

from openedx.adg.lms.webinars.tests.factories import WebinarRegistrationFactory


@pytest.mark.django_db
@pytest.mark.parametrize(
    'is_registered, is_team_member_registration, expected_call_count',
    [
        (False, False, 0), (True, False, 1), (False, True, 1),
    ]
)
def test_cancel_reminder_emails(mocker, is_registered, is_team_member_registration, expected_call_count):
    """
    Test that upon deleting webinar registration, reminder emails of a registered user
    or a webinar team member are cancelled
    """
    mock_cancel_all_reminders = mocker.patch('openedx.adg.lms.webinars.handlers.cancel_all_reminders')

    registration = WebinarRegistrationFactory(
        is_registered=is_registered, is_team_member_registration=is_team_member_registration)
    registration.delete()

    assert mock_cancel_all_reminders.call_count == expected_call_count
