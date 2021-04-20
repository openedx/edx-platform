"""
Helpers for webinars app
"""
from itertools import chain

from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email


def send_webinar_emails(template_slug, webinar_title, webinar_description, webinar_start_time, recipient_emails):
    """
    Send webinar email to the list of given email addresses using the given template and data

    Arguments:
        template_slug (str): Slug for the chosen email template
        webinar_title (str): Title of the webinar
        webinar_description (str): Description of the webinar
        webinar_start_time (Datetime): Start datetime of the webinar
        recipient_emails (list):  List of email addresses (str) to send the email to

    Returns:
        None
    """
    context = {
        'webinar_title': webinar_title,
        'webinar_description': webinar_description,
        'webinar_start_time': webinar_start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }

    task_send_mandrill_email.delay(template_slug, recipient_emails, context)


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


def validate_email_list(emails):
    """
    Validate list of comma separated email addresses

    Arguments:
         emails (str): string of comma separated emails

    Returns:
        error (boolean): True if error is found, False otherwise
        emails (list): list of parsed emails
    """

    emails = [email.strip() for email in emails.split(',') if email.strip()]

    for email in emails:
        try:
            validate_email(email)
        except ValidationError:
            return True, emails

    return False, emails


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
    return emails


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
