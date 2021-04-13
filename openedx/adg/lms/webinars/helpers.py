"""
Helpers for webinars app
"""
from itertools import chain

from openedx.adg.common.lib.mandrill_client.client import MandrillClient
from openedx.adg.common.lib.mandrill_client.tasks import task_send_mandrill_email


def _send_webinar_cancellation_emails(webinar_title, webinar_description, webinar_start_time, recipient_emails):
    """
    Send webinar cancellation email to the list of given email addresses

    Arguments:
        webinar_title (str): Title of the cancelled webinar
        webinar_description (str): Description of the cancelled webinar
        webinar_start_time (Datetime): Start datetime of the cancelled webinar
        recipient_emails (list):  List of Email addresses (str) to send the email to

    Returns:
        None
    """
    context = {
        'webinar_title': webinar_title,
        'webinar_description': webinar_description,
        'webinar_start_time': webinar_start_time.strftime("%B %d, %Y %I:%M %p %Z")
    }

    task_send_mandrill_email.delay(MandrillClient.WEBINAR_CANCELLATION, recipient_emails, context)


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

        _send_webinar_cancellation_emails(
            cancelled_webinar.title,
            cancelled_webinar.description,
            cancelled_webinar.start_time,
            list(webinar_email_addresses)
        )
