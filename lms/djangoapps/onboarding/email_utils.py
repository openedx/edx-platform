import base64

from crum import get_current_request
from openedx.core.lib.request_utils import safe_get_host
from common.lib.mandrill_client.client import MandrillClient
from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.tasks import task_send_hubspot_email


def send_admin_activation_email(first_name, org_id, org_name, claimed_by_name, claimed_by_email, dest_addr, hash_key):
    """
    Send an admin activation email.
    """
    request = get_current_request()
    encoded_org_id = base64.b64encode(str(org_id))
    admin_activation_link_raw = '{protocol}://{site}/onboarding/admin_activate/{activation_key}?admin_activation=True'
    admin_activation_link = admin_activation_link_raw.format(
        protocol='https' if request.is_secure() else 'http',
        site=safe_get_host(request),
        org_id=encoded_org_id,
        activation_key=hash_key.activation_hash
    )

    context = {
        'emailId': HubSpotClient.ORG_ADMIN_ACTIVATION,
        'message': {
            'to': dest_addr
        },
        'customProperties': {
            'first_name': first_name,
            'key': hash_key.activation_hash,
            'org_id': encoded_org_id,
            'org_name': org_name,
            'referring_user': hash_key.suggested_by.username,
            'claimed_by_name': claimed_by_name,
            'claimed_by_email': claimed_by_email,
            'admin_activation_link': admin_activation_link
        }
    }

    task_send_hubspot_email.delay(context)


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

    context = {
        'emailId': HubSpotClient.ORG_ADMIN_CHANGE,
        'message': {
            'to': dest_addr
        },
        'customProperties': {
            'first_name': org_admin_name,
            'org_name': org_name,
            'claimed_by_name': claimed_by_name,
            'claimed_by_email': claimed_by_email,
            'admin_activation_link': admin_activation_link
        }
    }

    task_send_hubspot_email.delay(context)


def send_admin_update_confirmation_email(org_name, current_admin, new_admin, confirm):
    """
    Send an email to the claimed admin, that he is either accepted as admin or rejected

    Arguments:
    org_name -- the name of the organization
    current_admin -- the current admin of the organization
    new_admin -- the new admin of the organization
    confirm -- 1 if the current_admin has confirmed resignation else 0
    """
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
        org_admin_get_in_touch_email_context = {
            'emailId': HubSpotClient.ORG_ADMIN_GET_IN_TOUCH,
            'message': {
                'to': current_admin.email
            },
            'customProperties': {
                'first_name': current_admin.first_name,
                'org_name': org_name,
                'claimed_by_name': '{first_name} {last_name}'.format(
                    first_name=new_admin.first_name,
                    last_name=new_admin.last_name
                ),
                'claimed_by_email': new_admin.email,
            }
        }
        task_send_hubspot_email.delay(org_admin_get_in_touch_email_context)

        org_new_admin_get_in_touch_email_context = {
            'emailId': HubSpotClient.ORG_NEW_ADMIN_GET_IN_TOUCH,
            'message': {
                'to': new_admin.email
            },
            'customProperties': {
                'first_name': new_admin.first_name,
                'org_name': org_name,
                'current_admin': current_admin.email,
            }
        }
        task_send_hubspot_email.delay(org_new_admin_get_in_touch_email_context)
