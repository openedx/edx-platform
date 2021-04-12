"""
Tests for all the helpers in webinars app
"""
import mock
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.webinars.helpers import (
    _send_webinar_cancellation_emails,
    send_cancellation_emails_for_given_webinars
)

from .constants import DUMMY_CONTEXT, DUMMY_DESCRIPTION, DUMMY_EMAIL_ADDRESSES, DUMMY_START_DATE, DUMMY_TITLE
from .factories import WebinarFactory, WebinarRegistrationFactory


@mock.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')
def test_send_webinar_cancellation_emails(mocked_task_send_mandrill_email):
    """
    Check if the cancellation email is being sent correctly with the given context and addresses
    """
    _send_webinar_cancellation_emails(DUMMY_TITLE, DUMMY_DESCRIPTION, DUMMY_START_DATE, DUMMY_EMAIL_ADDRESSES)

    mocked_task_send_mandrill_email.delay.assert_called_with(
        MandrillClient.WEBINAR_CANCELLATION, DUMMY_EMAIL_ADDRESSES, DUMMY_CONTEXT)


@pytest.mark.django_db
@mock.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')
@pytest.mark.parametrize(
    'registered_users_with_response, expected_email_addresses',
    [
        ([], []),
        ([(DUMMY_EMAIL_ADDRESSES[0], False), (DUMMY_EMAIL_ADDRESSES[1], False)], []),
        ([(DUMMY_EMAIL_ADDRESSES[0], True), (DUMMY_EMAIL_ADDRESSES[1], True)], DUMMY_EMAIL_ADDRESSES),
        ([(DUMMY_EMAIL_ADDRESSES[0], True), (DUMMY_EMAIL_ADDRESSES[1], False)], [DUMMY_EMAIL_ADDRESSES[0]])
    ]
)
def test_send_cancellation_emails_for_given_webinars(
    mocked_task_send_mandrill_email, registered_users_with_response, expected_email_addresses
):
    """
    Test if emails are sent to different registered users
    """
    webinar = WebinarFactory(title=DUMMY_TITLE, description=DUMMY_DESCRIPTION, start_time=DUMMY_START_DATE)
    for registered_user_with_response in registered_users_with_response:
        email, invite_response = registered_user_with_response
        test_user = UserFactory(email=email)
        WebinarRegistrationFactory(user=test_user, webinar=webinar, is_registered=invite_response)

    send_cancellation_emails_for_given_webinars([webinar])

    if expected_email_addresses:
        mocked_task_send_mandrill_email.delay.assert_called_with(
            MandrillClient.WEBINAR_CANCELLATION, expected_email_addresses, DUMMY_CONTEXT)
