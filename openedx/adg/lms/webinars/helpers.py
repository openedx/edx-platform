"""
Helpers for webinars app
"""
from django.apps import apps

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
    Sends emails for all the registered users for the given cancelled webinars

    Arguments:
        cancelled_webinars (iterable): Webinars for which to send the cancellation emails

    Returns:
        None
    """
    WebinarRegistration = apps.get_model(app_label='webinars', model_name='WebinarRegistration')

    for cancelled_webinar in cancelled_webinars:
        registered_user_emails = WebinarRegistration.objects.filter(
            webinar_id=cancelled_webinar.id, is_registered=True
        ).values_list('user__email', flat=True)

        if not registered_user_emails:
            continue

        _send_webinar_cancellation_emails(
            cancelled_webinar.title,
            cancelled_webinar.description,
            cancelled_webinar.start_time,
            list(registered_user_emails)
        )
