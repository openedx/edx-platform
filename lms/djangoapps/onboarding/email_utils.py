import base64

from django.core import mail
from django.conf import settings
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from smtplib import SMTPException


def send_admin_activation_email(org_id, org_name, dest_addr, hash_key):
    """
    Send an admin activation email.
    """
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    subject = "Admin Activation."
    encoded_org_id = base64.b64encode(str(org_id))

    message_context = {
        "key": hash_key.activation_hash,
        "org_id": encoded_org_id,
        "org_name": org_name,
        "referring_user": hash_key.suggested_by.username,

    }
    message_body = render_to_string('emails/admin_activation.txt', message_context)

    from_address = configuration_helpers.get_value(
        'email_from_address',
        settings.DEFAULT_FROM_EMAIL
    )

    while max_retries > 0:
        try:
            mail.send_mail(subject, message_body, from_address, [dest_addr], fail_silently=False)
            max_retries = 0
        except SMTPException:
            max_retries -= 1
        except Exception:
            max_retries -= 1
