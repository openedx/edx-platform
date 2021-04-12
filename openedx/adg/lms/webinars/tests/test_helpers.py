"""
Tests for all the helpers in webinars app
"""
import mock
import pytest

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.webinars.helpers import send_cancellation_emails_for_given_webinars

from .factories import WebinarFactory, WebinarRegistrationFactory


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')
@pytest.mark.parametrize(
    'registered_users_with_response, expected_email_addresses',
    [
        ([], []),
        ([("test1@example.com", False), ("test2@example.com", False)], []),
        ([("test1@example.com", True), ("test2@example.com", False)], ["test1@example.com"]),
        ([("test1@example.com", False), ("test2@example.com", True)], ["test2@example.com"]),
        ([("test1@example.com", True), ("test2@example.com", True)], ["test1@example.com", "test2@example.com"])
    ]
)
def test_send_cancellation_emails_for_given_webinars(
    mocked_task_send_mandrill_email, registered_users_with_response, expected_email_addresses
):
    """
    Test if emails are sent to different registered users
    """
    webinar = WebinarFactory()
    for email, invite_response in registered_users_with_response:
        WebinarRegistrationFactory(user__email=email, webinar=webinar, is_registered=invite_response)

    send_cancellation_emails_for_given_webinars([webinar])

    context = {
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }

    if expected_email_addresses:
        mocked_task_send_mandrill_email.delay.assert_called_with(
            MandrillClient.WEBINAR_CANCELLATION, expected_email_addresses, context)
