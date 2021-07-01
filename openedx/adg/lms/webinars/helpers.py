"""
Helpers for webinars app
"""
from datetime import datetime, timedelta
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.urls import reverse

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.common.lib.mandrill_client.tasks import task_cancel_mandrill_emails, task_send_mandrill_email
from openedx.adg.lms.helpers import convert_date_time_zone_and_format
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

from .constants import (
    ONE_WEEK_REMINDER_ID_FIELD_NAME,
    STARTING_SOON_REMINDER_ID_FIELD_NAME,
    WEBINAR_DATE_TIME_FORMAT,
    WEBINAR_DEFAULT_TIME_ZONE,
    WEBINARS_TIME_FORMAT
)


def send_webinar_emails(template_slug, webinar, recipient_emails, send_at=None):
    """
    Send webinar email to the list of given email addresses using the given template and data

    Arguments:
        template_slug (str): Slug for the chosen email template
        webinar (Webinar): Webinar object
        recipient_emails (list):  List of email addresses (str) to send the email to
        send_at (str): A String containing the time at which email will be sent

    Returns:
        None
    """
    context = {
        'webinar_id': webinar.id,
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_start_time': webinar.start_date_time_AST,
        'webinar_link': webinar.meeting_link,
    }

    if template_slug == MandrillClient.WEBINAR_CREATED:
        context['register_link'] = get_webinar_description_link(webinar.id)

    task_send_mandrill_email.delay(template_slug, recipient_emails, context, send_at)


def get_webinar_description_link(webinar_pk):
    """
    Return absolute url of webinar description page to use in webinar invitation emails

    Arguments:
        webinar_pk (int): Webinar primary key

    Returns:
        str: absolute url
    """
    root_url = configuration_helpers.get_value('LMS_ROOT_URL', settings.LMS_ROOT_URL)
    webinar_description_url = reverse('webinar_event', kwargs={'pk': webinar_pk})
    return f'{root_url}{webinar_description_url}'


def send_cancellation_emails_for_given_webinars(cancelled_webinars):
    """
    Sends emails for all the registered users, co-hosts, panelists and the presenter for the given cancelled webinars

    Arguments:
        cancelled_webinars (iterable): Webinars for which to send the cancellation emails

    Returns:
        None
    """
    for cancelled_webinar in cancelled_webinars:
        registered_user_emails = cancelled_webinar.registrations.filter(
            is_registered=True).values_list('user__email', flat=True)
        co_hosts = cancelled_webinar.co_hosts.all().values_list('email', flat=True)
        panelists = cancelled_webinar.panelists.all().values_list('email', flat=True)
        presenter_email_address = cancelled_webinar.presenter.email

        webinar_email_addresses = set(chain(co_hosts, panelists, registered_user_emails, {presenter_email_address}))

        if not webinar_email_addresses:
            continue

        send_webinar_emails(
            MandrillClient.WEBINAR_CANCELLATION,
            cancelled_webinar,
            list(webinar_email_addresses)
        )


def cancel_reminders_for_given_webinars(webinars):
    """
    Cancels all the reminders for the given webinars.

    Args:
        webinars (list): List of webinars for which reminders will be cancelled.

    Returns:
        None
    """
    for webinar in webinars:
        cancel_all_reminders(
            webinar.registrations.webinar_team_and_active_user_registrations()
        )


def send_webinar_registration_email(webinar, email):
    """
    Send webinar registration email to user.

    Args:
        webinar (Webinar): The webinar in which user is registered
        email (str): User's email

    Returns:
        None
    """
    task_send_mandrill_email.delay(MandrillClient.WEBINAR_REGISTRATION_CONFIRMATION, [email], {
        'webinar_title': webinar.title,
        'webinar_description': webinar.description,
        'webinar_link': webinar.meeting_link,
        'webinar_start_time': webinar.start_date_time_AST
    })


def schedule_webinar_reminders(user_emails, email_context):
    """
    Schedule reminders for a webinar on mandrill.

    Args:
        user_emails (list): List of user emails to schedule reminders.
        email_context (dict): Webinar reminders context.

    Returns:
        None
    """
    webinar_start_time = datetime.strptime(email_context['webinar_start_time'], WEBINARS_TIME_FORMAT)
    email_context['webinar_start_time'] = convert_date_time_zone_and_format(
        webinar_start_time, WEBINAR_DEFAULT_TIME_ZONE, WEBINAR_DATE_TIME_FORMAT
    )

    task_send_mandrill_email.delay(
        MandrillClient.WEBINAR_TWO_HOURS_REMINDER,
        user_emails,
        email_context,
        webinar_start_time - timedelta(hours=2),
        save_mandrill_msg_ids=True
    )

    if (webinar_start_time - timedelta(days=6)) > datetime.now():
        task_send_mandrill_email.delay(
            MandrillClient.WEBINAR_ONE_WEEK_REMINDER,
            user_emails,
            email_context,
            webinar_start_time - timedelta(days=7),
            save_mandrill_msg_ids=True
        )


def save_scheduled_reminder_ids(mandrill_response, template_name, webinar_reminders_context):
    """
    Saves mandrill msg ids of the reminders for a webinar registration.

    Args:
        mandrill_response (list): List containing the response from mandrill
        template_name (str): Mandrill email template slug
        webinar_reminders_context (dict): Webinar reminders context.

    Returns:
        None
    """
    from openedx.adg.lms.webinars.models import WebinarRegistration

    template_name_to_field_map = {
        MandrillClient.WEBINAR_TWO_HOURS_REMINDER: STARTING_SOON_REMINDER_ID_FIELD_NAME,
        MandrillClient.WEBINAR_ONE_WEEK_REMINDER: ONE_WEEK_REMINDER_ID_FIELD_NAME,
    }

    for response in mandrill_response:
        registration = WebinarRegistration.objects.filter(
            user__email=response['email'], webinar__id=webinar_reminders_context['webinar_id']
        ).first()
        setattr(registration, template_name_to_field_map[template_name], response['_id'])
        registration.save()


def extract_emails_from_string(emails_string):
    """
    Get a list of emails from a string with comma separated emails

    Arguments:
        emails_string (str): string of comma separated emails

    Returns:
        list: List of emails
    """
    emails = [email.strip() for email in emails_string.split(',') if email.strip()]
    return emails


def validate_email_list(emails):
    """
    Validate a list of email addresses

    Arguments:
         emails (str): String containing emails to validate

    Returns:
        error (boolean): True if error is found, False otherwise
    """

    emails = extract_emails_from_string(emails)

    for email in emails:
        try:
            validate_email(email)
        except ValidationError:
            return True

    return False


def webinar_emails_for_panelists_co_hosts_and_presenter(webinar):
    """
    Given a webinar, generate a list of emails for co-hosts, panelists, and presenter

    Arguments:
         webinar (obj): webinar object

    Returns:
        emails (list): list of all emails
    """

    panelist_emails = list(webinar.panelists.exclude(email='').values_list('email', flat=True))
    co_host_emails = list(webinar.co_hosts.exclude(email='').values_list('email', flat=True))
    emails = panelist_emails + co_host_emails
    if webinar.presenter:
        emails.append(webinar.presenter.email)
    return list(set(emails))


def remove_emails_duplicate_in_other_list(email_list, reference_email_list):
    """
    Remove emails from email_list that are already present in reference_email_list

    Arguments:
        email_list (list): list of emails to verify for duplication
        reference_email_list (list):  list of emails to use as a reference point

    Returns:
        emails (list): list of remaining emails
    """
    return [email for email in email_list if email not in reference_email_list]


def get_newly_added_and_removed_team_members(webinar_form, old_webinar):
    """
    Returns a list of newly added and removed co-hosts, panelists and presenter

    Arguments:
        webinar_form (Form): Model form with updated data.
        old_webinar (Webinar): Old webinar state prior to updation.

    Returns:
        new_members (list): list of newly added co-hosts, panelists and presenter
        removed_members (list): list of removed co-hosts, panelists and presenter
    """
    cleaned_data = webinar_form.cleaned_data

    old_team = old_webinar.webinar_co_hosts_and_panelists()
    old_team.add(old_webinar.presenter)

    new_team = set(chain(cleaned_data['co_hosts'], cleaned_data['panelists'], {cleaned_data['presenter']}))

    new_members = list(new_team - old_team)
    removed_members = list(old_team - new_team)

    return new_members, removed_members


def cancel_all_reminders(registrations, is_rescheduling=False):
    """
    Cancels reminders by extracting msg ids from the given registrations. In case the `is_rescheduling` is `True`, we
    will not run the task `task_cancel_mandrill_emails` asynchronously.

    Args:
        is_rescheduling (bool): It shows whether we are rescheduling emails or just cancelling them.
        registrations (list): List of registrations for which reminders will be cancelled.

    Returns:
        None
    """
    from openedx.adg.lms.webinars.models import WebinarRegistration

    msg_id_map = {
        'starting_soon_msg_ids': [],
        'one_week_before_msg_ids': [],
    }

    for registration in registrations:
        if registration.starting_soon_mandrill_reminder_id:
            msg_id_map['starting_soon_msg_ids'].append(registration.starting_soon_mandrill_reminder_id)
            registration.starting_soon_mandrill_reminder_id = ''

        if registration.week_before_mandrill_reminder_id:
            msg_id_map['one_week_before_msg_ids'].append(registration.week_before_mandrill_reminder_id)
            registration.week_before_mandrill_reminder_id = ''

    if is_rescheduling:
        task_cancel_mandrill_emails(msg_id_map['starting_soon_msg_ids'])
        task_cancel_mandrill_emails(msg_id_map['one_week_before_msg_ids'])
    else:
        task_cancel_mandrill_emails.delay(msg_id_map['starting_soon_msg_ids'])
        task_cancel_mandrill_emails.delay(msg_id_map['one_week_before_msg_ids'])

    WebinarRegistration.objects.bulk_update(
        registrations, ['starting_soon_mandrill_reminder_id', 'week_before_mandrill_reminder_id'], batch_size=999
    )


def get_webinar_invitees_emails(webinar_form):
    """
    Given a webinar form, get emails of all invitees of the webinar

    Arguments:
        webinar_form (Form): Model form with updated data.

    Returns:
        list: Webinar invitees' emails
    """
    comma_seperated_emails = webinar_form.cleaned_data.get('invites_by_email_address')
    webinar_invitees_emails = extract_emails_from_string(comma_seperated_emails)
    if webinar_form.cleaned_data.get('invite_all_platform_users'):
        webinar_invitees_emails += list(
            User.objects.exclude(email='').values_list('email', flat=True)
        )

    return webinar_invitees_emails
