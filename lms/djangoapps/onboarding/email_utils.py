import base64

from django.core import mail
from django.conf import settings
from util.request import safe_get_host
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

    site = safe_get_host(request)
    if request.is_secure():
        admin_activation_link = 'https://' + site + '/onboarding/admin_activate/' + encoded_org_id + '/' + hash_key.activation_hash
    else:
        admin_activation_link = 'http://' + site + '/onboarding/admin_activate/' + encoded_org_id + '/' + hash_key.activation_hash

    message_context["activation_link"] = admin_activation_link

    while max_retries > 0:
        try:
            MandrillClient().send_mail(MandrillClient.ORG_ADMIN_ACTIVATION_TEMPLATE, dest_addr, message_context)
            max_retries = 0
        except:
            max_retries -= 1
