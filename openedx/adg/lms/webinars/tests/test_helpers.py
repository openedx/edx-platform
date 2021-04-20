"""
All test cases for webinars app helpers
"""
from datetime import datetime

import factory
import pytest

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.webinars.helpers import (
    remove_emails_duplicate_in_other_list,
    send_cancellation_emails_for_given_webinars,
    send_webinar_emails,
    send_webinar_registration_email,
    validate_email_list,
    webinar_emails_for_panelists_co_hosts_and_presenter
)

from .constants import (
    CO_HOST_1,
    CO_HOST_2,
    INVALID_EMAIL_ADDRESSES,
    PANELIST_1,
    PANELIST_2,
    PRESENTER,
    VALID_EMAIL_ADDRESSES
)
from .factories import WebinarFactory, WebinarRegistrationFactory


@pytest.mark.django_db
def test_send_webinar_emails(mocker):
    """
    Test if `send_webinar_emails` is sending the email with the correct data
    """
    mocked_task_send_mandrill_email = mocker.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')

    webinar = WebinarFactory()
    send_webinar_emails("test_slug", webinar.title, webinar.description, webinar.start_time, "t1@eg.com")

    expected_context = {
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }
    mocked_task_send_mandrill_email.delay.assert_called_with("test_slug", "t1@eg.com", expected_context)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'registered_users_with_response, cohosts, panelists, presenter, expected_email_addresses',
    [
        (
            [], [], [], 't3@eg.com', ['t3@eg.com']
        ),
        (
            [('t1@eg.com', False), ('t2@eg.com', False)], [], [], 't3@eg.com', ['t3@eg.com']
        ),
        (
            [('t1@eg.com', True), ('t2@eg.com', False)], ['t1@eg.com'], [], 't3@eg.com', ['t1@eg.com', 't3@eg.com']
        ),
        (
            [('t1@eg.com', False), ('t2@eg.com', True)], [], ['t2@eg.com'], 't3@eg.com', ['t2@eg.com', 't3@eg.com']
        ),
        (
            [('t1@eg.com', False), ('t2@eg.com', False)], ['t1@eg.com'], ['t2@eg.com'], 't3@eg.com',
            ['t1@eg.com', 't2@eg.com', 't3@eg.com']
        ),
        (
            [('t1@eg.com', True), ('t2@eg.com', True)], ['t4@eg.com'], ['t4@eg.com'], 't3@eg.com',
            ['t1@eg.com', 't2@eg.com', 't3@eg.com', 't4@eg.com']
        ),
        (
            [('t1@eg.com', True), ('t2@eg.com', True)], ['t4@eg.com'], ['t5@eg.com'], 't3@eg.com',
            ['t1@eg.com', 't2@eg.com', 't3@eg.com', 't4@eg.com', 't5@eg.com']
        ),
        (
            [('t1@eg.com', True)], ['t4@eg.com', 't5@eg.com'], ['t5@eg.com', 't6@eg.com'], 't3@eg.com',
            ['t1@eg.com', 't3@eg.com', 't4@eg.com', 't5@eg.com', 't6@eg.com']
        )
    ]
)
def test_send_cancellation_emails_for_given_webinars(
    mocker, registered_users_with_response, cohosts, panelists, presenter, expected_email_addresses
):
    """
    Test if emails are sent to all the registered users, co-hosts, panelists and the presenter without any duplicates
    """
    mocked_task_send_mandrill_email = mocker.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')

    webinar = WebinarFactory(presenter__email=presenter)
    for email, invite_response in registered_users_with_response:
        WebinarRegistrationFactory(user__email=email, webinar=webinar, is_registered=invite_response)

    cohost_emails = factory.Iterator(cohosts)
    cohost_users = UserFactory.create_batch(len(cohosts), email=cohost_emails)
    webinar.co_hosts.add(*cohost_users)

    panelist_emails = factory.Iterator(panelists)
    panelist_users = UserFactory.create_batch(len(panelists), email=panelist_emails)
    webinar.panelists.add(*panelist_users)

    send_cancellation_emails_for_given_webinars([webinar])

    expected_context = {
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }

    actual_template, actual_email_addresses, actual_context = mocked_task_send_mandrill_email.delay.call_args.args

    assert actual_template == MandrillClient.WEBINAR_CANCELLATION
    assert actual_context == expected_context
    assert sorted(actual_email_addresses) == sorted(expected_email_addresses)


@pytest.mark.django_db
def test_send_webinar_registration_email(mocker):
    """
    Test sending webinar registration email to user
    """
    mock_task = mocker.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email.delay')
    webinar = WebinarFactory(start_time=datetime(2020, 1, 1, 13, 10, 1))
    email = 'email@example.com'

    send_webinar_registration_email(webinar, email)

    mock_task.assert_called_once_with(MandrillClient.WEBINAR_REGISTRATION_CONFIRMATION, [email], {
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_link': webinar.meeting_link,
        'webinar_start_time': 'Jan 01, 2020 01:10 PM GMT',
    })


@pytest.mark.parametrize(
    'emails , expected_error', [
        (VALID_EMAIL_ADDRESSES, False),
        (INVALID_EMAIL_ADDRESSES, True)
    ]
)
def test_validate_email_list(emails, expected_error):
    """
    Test if 'validate_email_list' returns error when emails are invalid
    """
    assert validate_email_list(emails)[0] == expected_error


@pytest.mark.django_db
@pytest.mark.parametrize(
    'panelists, co_hosts, presenter, expected_emails', [
        ([PANELIST_1, PANELIST_2], [], PRESENTER, [PANELIST_1, PANELIST_2, PRESENTER]),
        ([], [CO_HOST_1, CO_HOST_2], PRESENTER, [CO_HOST_1, CO_HOST_2, PRESENTER]),
        ([], [], PRESENTER, [PRESENTER]),
        (
            [PANELIST_1, PANELIST_2],
            [CO_HOST_1, CO_HOST_2],
            PRESENTER,
            [PANELIST_1, PANELIST_2, CO_HOST_1, CO_HOST_2, PRESENTER]
        ),
    ]
)
def test_webinar_emails_for_panelists_co_hosts_and_presenter(webinar, panelists, co_hosts, presenter, expected_emails):
    """
    Test if 'webinar_emails_for_panelists_co_hosts_and_presenter' returns the list of webinar related emails
    """
    panelist_emails = factory.Iterator(panelists)
    panelist_users = UserFactory.create_batch(len(panelists), email=panelist_emails)
    webinar.panelists.add(*panelist_users)

    co_host_emails = factory.Iterator(co_hosts)
    co_host_users = UserFactory.create_batch(len(co_hosts), email=co_host_emails)
    webinar.co_hosts.add(*co_host_users)

    webinar.presenter = UserFactory(email=presenter)
    assert sorted(webinar_emails_for_panelists_co_hosts_and_presenter(webinar)) == sorted(expected_emails)


@pytest.mark.django_db
@pytest.mark.parametrize(
    'emails, reference_emails, expected_emails', [
        ([], ['t1@eg.com', 't2@eg.com'], []),
        (['t1@eg.com', 't2@eg.com'], [], ['t1@eg.com', 't2@eg.com']),
        ([], [], []),
        (
            ['t1@eg.com', 't2@eg.com', 't3@eg.com'],
            ['t1@eg.com', 't2@eg.com', 't4@eg.com'],
            ['t3@eg.com']
        ),

    ]
)
def test_remove_emails_duplicate_in_other_list(emails, reference_emails, expected_emails):
    """
    Test that only the list of emails that are not present in reference list of emails are returned
    """
    assert sorted(remove_emails_duplicate_in_other_list(emails, reference_emails)) == sorted(expected_emails)
