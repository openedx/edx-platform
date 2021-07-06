"""
All test cases for webinars app helpers
"""
from datetime import datetime

import factory
import pytest
from mock import Mock

from common.djangoapps.student.tests.factories import UserFactory
from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.lms.webinars.constants import ONE_WEEK_REMINDER_ID_FIELD_NAME, STARTING_SOON_REMINDER_ID_FIELD_NAME
from openedx.adg.lms.webinars.helpers import (
    cancel_all_reminders,
    cancel_reminders_for_given_webinars,
    extract_emails_from_string,
    get_newly_added_and_removed_team_members,
    get_webinar_description_link,
    get_webinar_invitees_emails,
    remove_emails_duplicate_in_other_list,
    save_scheduled_reminder_ids,
    send_cancellation_emails_for_given_webinars,
    send_webinar_emails,
    send_webinar_registration_email,
    validate_email_list,
    webinar_emails_for_panelists_co_hosts_and_presenter
)

from .constants import (
    CO_HOST_1,
    CO_HOST_2,
    FAKE_MANDRILL_MSG_ID,
    INVALID_EMAIL_ADDRESSES,
    PANELIST_1,
    PANELIST_2,
    PRESENTER,
    VALID_EMAIL_ADDRESSES
)
from .factories import WebinarFactory, WebinarRegistrationFactory


@pytest.mark.django_db
@pytest.mark.parametrize('template_slug', ('test_slug', MandrillClient.WEBINAR_CREATED))
def test_send_webinar_emails(mocker, template_slug):
    """
    Test if `send_webinar_emails` is sending the email with the correct data
    """
    mocked_task_send_mandrill_email = mocker.patch('openedx.adg.lms.webinars.helpers.task_send_mandrill_email')

    webinar = WebinarFactory()
    send_webinar_emails(template_slug, webinar, ['t1@eg.com'])

    expected_context = {
        'webinar_id': webinar.id,
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_date_time_AST,
        'webinar_link': webinar.meeting_link,
    }

    if template_slug == MandrillClient.WEBINAR_CREATED:
        expected_context['register_link'] = get_webinar_description_link(webinar.id)

    mocked_task_send_mandrill_email.delay.assert_called_with(template_slug, ['t1@eg.com'], expected_context, None)


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
        'webinar_id': webinar.id,
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_date_time_AST,
        'webinar_link': webinar.meeting_link,
    }

    actual_template, actual_email_addresses, actual_context, _ = mocked_task_send_mandrill_email.delay.call_args.args

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
        'webinar_start_time': 'Wednesday, January 01, 2020 04:10 PM AST',
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
    assert validate_email_list(emails) == expected_error


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


@pytest.mark.django_db
@pytest.mark.parametrize(
    'template, msg_id_field_name', [
        (MandrillClient.WEBINAR_TWO_HOURS_REMINDER, STARTING_SOON_REMINDER_ID_FIELD_NAME),
        (MandrillClient.WEBINAR_ONE_WEEK_REMINDER, ONE_WEEK_REMINDER_ID_FIELD_NAME),
    ]
)
def test_save_scheduled_reminder_ids(template, msg_id_field_name, webinar_registration):
    """
    Tests save_scheduled_reminder_ids method is saving reminder ids properly.
    """
    mandrill_response = [
        {
            '_id': FAKE_MANDRILL_MSG_ID,
            'email': webinar_registration.user.email
        }
    ]
    webinar_reminders_context = {'webinar_id': webinar_registration.webinar.id}

    save_scheduled_reminder_ids(mandrill_response, template, webinar_reminders_context)

    webinar_registration.refresh_from_db()
    assert getattr(webinar_registration, msg_id_field_name) == FAKE_MANDRILL_MSG_ID


@pytest.mark.django_db
def test_cancel_reminders_for_given_webinars(webinar, mocker):
    """
    Tests `cancel_all_reminders` is called for the webinar to cancel reminder emails.
    """
    mock_cancel_reminders = mocker.patch('openedx.adg.lms.webinars.helpers.cancel_all_reminders')

    cancel_reminders_for_given_webinars([webinar])

    mock_cancel_reminders.assert_called_once()


@pytest.mark.parametrize(
    'msg_id_field_name, msg_id, is_rescheduling', [
        (STARTING_SOON_REMINDER_ID_FIELD_NAME, FAKE_MANDRILL_MSG_ID, True),
        (ONE_WEEK_REMINDER_ID_FIELD_NAME, FAKE_MANDRILL_MSG_ID, False),
    ]
)
@pytest.mark.django_db
def test_cancel_all_reminders(msg_id, msg_id_field_name, webinar_registration, mocker, is_rescheduling):
    """
    Tests `task_cancel_mandrill_emails` is called to cancel reminder emails.
    """
    mock_task_cancel_reminders = mocker.patch('openedx.adg.lms.webinars.helpers.task_cancel_mandrill_emails')

    setattr(webinar_registration, msg_id_field_name, msg_id)
    cancel_all_reminders([webinar_registration], is_rescheduling)

    if is_rescheduling:
        assert mock_task_cancel_reminders.call_count == 2
    else:
        assert mock_task_cancel_reminders.delay.call_count == 2


@pytest.mark.django_db
@pytest.mark.parametrize('emails_string, expected_emails', [
    ('', []),
    ('  test1@email.com  ', ['test1@email.com']),
    ('test1@email.com,test2@email.com', ['test1@email.com', 'test2@email.com'])
], ids=['no_email_input', 'email_with_extra_spaces_input', 'multiple_emails_input'])
def test_extract_emails_from_string(emails_string, expected_emails):
    """
    Tests that the `extract_emails_from_string` returns the email addresses in a list correctly
    """
    actual_emails = extract_emails_from_string(emails_string)
    assert actual_emails == expected_emails


@pytest.mark.django_db
@pytest.mark.parametrize('invite_all_platform_users', [True, False])
def test_get_webinar_invitees_emails(invite_all_platform_users, webinar):
    """
    Test that `get_webinar_invitees_emails` correctly returns the invitees' emails of a webinar
    """
    UserFactory(email='learner@email.com')

    mock_webinar_form = Mock()
    mock_webinar_form.instance = webinar
    mock_webinar_form.cleaned_data = {
        'invites_by_email_address': 'guest1@email.com, guest2@email.com',
        'invite_all_platform_users': invite_all_platform_users
    }

    if invite_all_platform_users:
        expected_emails = {
            webinar.presenter.email,
            webinar.created_by.email,
            'learner@email.com',
            'guest1@email.com',
            'guest2@email.com'
        }
    else:
        expected_emails = {'guest1@email.com', 'guest2@email.com'}

    actual_emails = set(get_webinar_invitees_emails(mock_webinar_form))

    assert expected_emails == actual_emails


@pytest.mark.django_db
def test_get_newly_added_and_removed_team_members(webinar):
    """
    Test that the function `get_newly_added_and_removed_team_members` correctly extracts newly added and removed members
    from a webinar form
    """
    mock_webinar_form = Mock()

    users = UserFactory.create_batch(8)
    webinar.presenter = users[0]
    webinar.co_hosts.set(users[1:3])
    webinar.panelists.set(users[3:5])

    mock_webinar_form.cleaned_data = {
        'presenter': users[5],
        'co_hosts': [users[1], users[6]],
        'panelists': [users[3], users[7]]
    }

    expected_new_members = set(users[5:8])
    expected_removed_members = {users[0], users[2], users[4]}

    actual_new_members, actual_removed_members = get_newly_added_and_removed_team_members(mock_webinar_form, webinar)

    assert expected_new_members == set(actual_new_members)
    assert expected_removed_members == set(actual_removed_members)
