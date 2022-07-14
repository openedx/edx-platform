"""
HubSpot client tasks
"""
import logging

from celery.task import task
from django.contrib.auth.models import User

from common.lib.hubspot_client.client import HubSpotClient
from common.lib.hubspot_client.helpers import prepare_user_data_for_hubspot_contact_creation
from lms.djangoapps.onboarding.models import UserExtendedProfile


logger = logging.getLogger(__name__)


@task()
def task_send_hubspot_email(data):
    """
    Task to send email using HubSpot Client.
    """
    HubSpotClient().send_mail(data)


@task
def task_create_or_update_hubspot_contact(user_email, user_json, is_contact_created=False):
    """
    Task to Create or Update marketing contact on HubSpot.

    Following steps are being performed:
    1. Update contact on HubSpot if we have the HubSpot id of contact.
    2. If contact is not synced before then try to create contact on HubSpot.
        i. If contact creation is successful, save the HubSpot Contact id.
        ii. If we get an error that contact already exists with the email then save the HubSpot Contact id and make an
            update request.

    Arguments:
        user_email (str): Email of user.
        user_json (dict): Data for HubSpot request.
        is_contact_created (bool): Is contact already synced with HubSpot.
    """
    logger.info('Syncing user data with HubSpot %s %s %s', user_email, user_json, is_contact_created)

    user = User.objects.filter(email=user_email).first()
    if not user:
        return

    client = HubSpotClient()
    if is_contact_created:
        client.update_contact(user, user_json)
        return

    response = client.create_contact(user_json)
    if response.status_code == 201:
        hubspot_contact_id = response.json()['id']
        UserExtendedProfile.objects.update_or_create(user=user, defaults={'hubspot_contact_id': hubspot_contact_id})

    elif response.status_code == 409:
        message = response.json().get('message')
        if message.startswith('Contact already exists.'):
            hubspot_contact_id = message.split(' ')[-1]
            UserExtendedProfile.objects.update_or_create(user=user, defaults={'hubspot_contact_id': hubspot_contact_id})
            client.update_contact(user, user_json)
        else:
            logger.exception(
                'Could not create or update HubSpot Contact. User: {user}, Data: {data}, Error Message: {msg}'.format(
                    user=user,
                    data=user_json,
                    msg=message
                )
            )
    else:
        logger.exception(
            'Could not create or update HubSpot Contact. User: {user}, Data: {data}'.format(user=user, data=user_json)
        )


@task()
def task_update_org_details_at_hubspot(org_label, org_type, work_area, org_id):
    """
    Update the details of the organization associated with the org_id

    Arguments:
        org_id (int): id of the target organization
        org_label (str): Label of the organization to update
        org_type (str): Type of the organization to update
        work_area (str): Work area of the organization to update
    """
    logger.info('Task to send organization details to HubSpot')
    logger.info(org_label)

    extended_profiles = UserExtendedProfile.objects.filter(organization_id=org_id).select_related('user')
    user_json = {
        'properties': {
            'edx_organization': org_label,
            'edx_organization_type': org_type,
            'edx_area_of_work': work_area
        }
    }

    for extended_profile in extended_profiles:
        user = extended_profile.user
        if not extended_profile.hubspot_contact_id:
            user_json = prepare_user_data_for_hubspot_contact_creation(extended_profile.user)

        task_create_or_update_hubspot_contact.delay(
            user.email, user_json, bool(extended_profile.hubspot_contact_id)
        )
