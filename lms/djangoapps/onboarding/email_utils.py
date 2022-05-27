import base64

from django.conf import settings
from crum import get_current_request
from openedx.core.lib.request_utils import safe_get_host
from common.lib.mandrill_client.client import MandrillClient


def send_admin_activation_email(first_name, org_id, org_name, claimed_by_name, claimed_by_email, dest_addr, hash_key):
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
        "claimed_by_name": claimed_by_name,
        "claimed_by_email": claimed_by_email,
    }

    admin_activation_link = '{protocol}://{site}/onboarding/admin_activate/{activation_key}?admin_activation=True'.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        org_id=encoded_org_id,
        activation_key=hash_key.activation_hash
    )
    message_context["admin_activation_link"] = admin_activation_link

    while max_retries > 0:
        try:
            # TODO: FIX MANDRILL EMAILS
            # MandrillClient().send_mail(MandrillClient.ORG_ADMIN_ACTIVATION_TEMPLATE, dest_addr, message_context)
            max_retries = 0
        except:
            max_retries -= 1


def send_admin_update_email(org_id, org_name, dest_addr, org_admin_name, hash_key, claimed_by_email, claimed_by_name):
    """
    Send an email to the admin, that this user claims himself to be the admin
    """
    request = get_current_request()

    admin_activation_link = '{protocol}://{site}/onboarding/admin_activate/{claimed_by_key}'.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        claimed_by_key=hash_key.activation_hash
    )

    message_context = {
        "org_name": org_name,
        "first_name": org_admin_name,
        "claimed_by_name": claimed_by_name,
        "claimed_by_email": claimed_by_email,
        "admin_activation_link": admin_activation_link
    }

    # TODO: FIX MANDRILL EMAILS
    # MandrillClient().send_mail(MandrillClient.ORG_ADMIN_CHANGE_TEMPLATE, dest_addr, message_context)


def send_admin_update_confirmation_email(org_name, current_admin, new_admin, confirm):
    """
    Send an email to the claimed admin, that he is either accepted as admin or rejected

    Arguments:
    org_name -- the name of the organization
    current_admin -- the current admin of the organization
    new_admin -- the new admin of the organization
    confirm -- 1 if the current_admin has confirmed resignation else 0
    """
    return

    # TODO: FIX MANDRILL EMAILS
    if confirm == 1:
        MandrillClient().send_mail(MandrillClient.ORG_ADMIN_CLAIM_CONFIRMATION, current_admin.email, {
            "first_name": current_admin.first_name,
            "org_name": org_name,
            "claimed_by_name": new_admin.email,
        })
        MandrillClient().send_mail(MandrillClient.NEW_ADMIN_CLAIM_CONFIRMATION, new_admin.email, {
            "first_name": new_admin.first_name,
            "org_name": org_name,
            "confirm": confirm,
        })
    else:
        MandrillClient().send_mail(MandrillClient.ORG_ADMIN_GET_IN_TOUCH, current_admin.email, {
            "first_name": current_admin.first_name,
            "org_name": org_name,
            "claimed_by_name": "{first_name} {last_name}".format(
                first_name=new_admin.first_name, last_name=new_admin.last_name
            ),
            "claimed_by_email": new_admin.email,
        })
        MandrillClient().send_mail(MandrillClient.NEW_ADMIN_GET_IN_TOUCH, new_admin.email, {
            "first_name": new_admin.first_name,
            "org_name": org_name,
            "current_admin": current_admin.email,
        })
