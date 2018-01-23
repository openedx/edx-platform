import base64

from django.core import mail
from django.conf import settings
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from smtplib import SMTPException
from common.lib.mandrill_client.client import MandrillClient


def send_admin_activation_email(first_name, org_id, org_name, dest_addr, hash_key):
    """
    Send an admin activation email.
    """
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    subject = "Admin Activation."
    encoded_org_id = base64.b64encode(str(org_id))

    message_context = {
        "first_name": first_name,
        "key": hash_key.activation_hash,
        "org_id": encoded_org_id,
        "org_name": org_name,
        "referring_user": hash_key.suggested_by.username,
    }
    admin_activation_link = render_to_string('emails/admin_activation_link.txt', message_context)

    message_context["key"] = admin_activation_link

    while max_retries > 0:
        try:
            MandrillClient().send_admin_activation_mail(dest_addr, message_context)
            max_retries = 0
        except:
            max_retries -= 1
