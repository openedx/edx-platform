import json
import logging
from smtplib import SMTPException

from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import get_template

log = logging.getLogger(__name__)
TEMPLATE_PATH = '{key}_email.html'


def send_notification(key, data, subject, from_email, dest_emails):
    """
    Send an email.

    params:
        key - Email template will be selected on the basis of key
        data - Dict containing context/data for the template
        subject - Email subject
        from_email - Email address to send email
        dest_emails - List of destination emails

    return: a boolean variable indicating email response.
    """
    content = json.dumps(data)
    email_template_path = TEMPLATE_PATH.format(key=key)
    html_content = get_template(email_template_path).render(data)
    msg = EmailMultiAlternatives(subject, content, from_email, dest_emails)
    msg.attach_alternative(html_content, "text/html")
    try:
        response = msg.send()
        log.info(
            'Email has been sent from "%s" to "%s" for content %s.',
            from_email,
            dest_emails,
            content
        )
        return response
    except SMTPException:
        log.error(
            'Unable to send an email from "%s" to %s for content "%s".',
            from_email,
            dest_emails,
            content
        )
        return False


def send_notification_email_to_support(subject, body, name, email, custom_fields=None, additional_info=None, course=None):
    """
    Sending a notification-email to the Support Team.
    """
    key = "support"
    dest_emails = settings.SUPPORT_DESK_EMAILS
    from_address = settings.DEFAULT_FROM_EMAIL
    data = {
        'name': name,
        'email': email,
        'body': body,
        'custom_fields': custom_fields,
        'additional_info': additional_info,
    }
    email_response = send_notification(
        key, data, subject, from_address, dest_emails)
    return email_response
