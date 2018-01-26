import base64

from django.core import mail
from django.conf import settings
from crum import get_current_request
from util.request import safe_get_host
from edxmako.shortcuts import render_to_string
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from smtplib import SMTPException
from common.lib.mandrill_client.client import MandrillClient


def send_admin_activation_email(first_name, org_id, org_name, dest_addr, hash_key):
    """
    Send an admin activation email.
    """

    request = get_current_request()
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    encoded_org_id = base64.b64encode(str(org_id))

    message_context = {
        "first_name": first_name,
        "key": hash_key.activation_hash,
        "org_id": encoded_org_id,
        "org_name": org_name,
        "referring_user": hash_key.suggested_by.username,
    }

    admin_activation_link = '{protocol}://{site}/onboarding/admin_activate/{org_id}/{activation_key}'.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        org_id=encoded_org_id,
        activation_key=hash_key.activation_hash
    )
    message_context["activation_link"] = admin_activation_link

    while max_retries > 0:
        try:
            MandrillClient().send_mail(MandrillClient.ORG_ADMIN_ACTIVATION_TEMPLATE, dest_addr, message_context)
            max_retries = 0
        except:
            max_retries -= 1

            
def send_admin_update_email(org_id, org_name, dest_addr, hash_key, claimed_by_email, claimed_by_name):
    """
    Send an email to the admin, that this user claims himself to be the admin
    """
    subject = "Admin Claim"

    message_context = {
        "org_name": org_name,
        "claimed_by_name": claimed_by_name,
        "claimed_by_key": hash_key.activation_hash,
        "claimed_by_email": claimed_by_email,
    }
    message_body_path = 'emails/admin_change.txt'

    send_email(subject, message_body_path, message_context, dest_addr)


def send_admin_update_confirmation_email(org_name, dest_addr, confirm):
    """
    Send an email to the claimed admin, that he is either accepted as admin or rejected
    """
    subject = "Admin Claim Request Confirmation"

    message_context = {
        "org_name": org_name,
        "confirm": confirm
    }
    message_body_path = 'emails/admin_change_confirmation.txt'

    send_email(subject, message_body_path, message_context, dest_addr)


def send_email(subject, message_body_path, message_context, dest_addr):
    max_retries = settings.RETRY_ACTIVATION_EMAIL_MAX_ATTEMPTS
    message_body = render_to_string(message_body_path, message_context)

    from_address = configuration_helpers.get_value('email_from_address', settings.DEFAULT_FROM_EMAIL)
    while max_retries > 0:
        try:
            mail.send_mail(subject, message_body, from_address, [dest_addr], fail_silently=False)
            max_retries = 0
        except SMTPException:
            max_retries -= 1
        except Exception:
            max_retries -= 1
    pass

