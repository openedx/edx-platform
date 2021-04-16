"""
Helpers for webinars app
"""
from datetime import timedelta
from itertools import chain

from django.utils.timezone import now

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email


def send_webinar_emails(
    template_slug,
    webinar_id,
    webinar_title,
    webinar_description,
    webinar_start_time,
    recipient_emails,
    send_at=None,
):
    """
    Send webinar email to the list of given email addresses using the given template and data

    Arguments:
        template_slug (str): Slug for the chosen email template
        webinar_id (int): Id of the webinar
        webinar_title (str): Title of the webinar
        webinar_description (str): Description of the webinar
        webinar_start_time (Datetime): Start datetime of the webinar
        recipient_emails (list):  List of email addresses (str) to send the email to
        send_at (str): A String containing the time at which email will be sent

    Returns:
        None
    """
    context = {
        'webinar_id': webinar_id,
        'webinar_title': webinar_title,
        'webinar_description': webinar_description,
        'webinar_start_time': webinar_start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }

    task_send_mandrill_email.delay(template_slug, recipient_emails, context, send_at)


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
            cancelled_webinar.id,
            cancelled_webinar.title,
            cancelled_webinar.description,
            cancelled_webinar.start_time,
            list(webinar_email_addresses)
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
        'webinar_start_time': webinar.start_time.strftime('%b %d, %Y %I:%M %p GMT'),
    })


def schedule_webinar_reminders(user_email, webinar):
    """
    Schedule reminders for a webinar on mandrill.

    Args:
        user_email (str): User email to schedule a reminder.
        webinar (Webinar): The webinar for which reminders will be scheduled.
    """
    send_webinar_emails(
        MandrillClient.WEBINAR_TWO_HOURS_REMINDER,
        webinar.id,
        webinar.title,
        webinar.description,
        webinar.start_time,
        [user_email],
        webinar.start_time - timedelta(hours=2),
    )

    week_before_webinar_start_time = webinar.start_time - timedelta(days=7)

    if week_before_webinar_start_time > now():
        send_webinar_emails(
            MandrillClient.WEBINAR_WEEK_BEFORE_REMINDER,
            webinar.id,
            webinar.title,
            webinar.description,
            webinar.start_time,
            [user_email],
            week_before_webinar_start_time,
        )


def reschedule_webinar_reminders(registrations, send_at, msg_id_field_name):
    """
    Reschedules reminders using the given field for msg ids.

    Args:
        registrations (list): List of webinar registrations.
        send_at (str): String containing time to schedules an email at.
        msg_id_field_name (str): String containing field name for the mandrill msg ids.
    """
    for registration in registrations:
        MandrillClient().reschedule_email(getattr(registration, msg_id_field_name), send_at)


def save_scheduled_reminder_ids(mandrill_response, template_name, webinar_id):
    """
    Saves mandrill msg ids of the reminders for a webinar registration.

    Args:
        webinar_id (int): Webinar Id
        mandrill_response (list): List containing the response from mandrill
        template_name (str): Mandrill email template slug
    """
    from openedx.adg.lms.webinars.models import WebinarRegistration

    template_name_to_field_map = {
        MandrillClient.WEBINAR_TWO_HOURS_REMINDER: 'starting_soon_mandrill_reminder_id',
        MandrillClient.WEBINAR_WEEK_BEFORE_REMINDER: 'week_before_mandrill_reminder_id',
    }

    for response in mandrill_response:
        registration = WebinarRegistration.objects.get(
            user__email=response['email'], webinar__id=webinar_id
        )
        setattr(registration, template_name_to_field_map[template_name], response['_id'])
        registration.save()
