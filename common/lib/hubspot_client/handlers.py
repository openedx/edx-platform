"""
Handlers and signals for Mailchimp pipeline
"""
from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from common.lib.hubspot_client.helpers import prepare_user_data_for_hubspot_contact_creation
from common.lib.hubspot_client.tasks import task_create_or_update_hubspot_contact, task_update_org_details_at_hubspot
from lms.djangoapps.onboarding.models import EmailPreference, Organization, UserExtendedProfile
from mailchimp_pipeline.helpers import (
    get_enrollements_course_short_ids,
    get_user_active_enrollements
)
from student.models import UserProfile

log = getLogger(__name__)


@receiver(post_save, sender=EmailPreference)
def sync_email_preference_with_hubspot(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver that syncs the chosen email preference of a user when triggered

    Arguments:
        sender: The particular object that triggered the receiver
        instance: Object that contains data regarding the user and their chosen preference

    Returns:
        None
    """
    opt_in = ''

    if instance.opt_in == 'yes':
        opt_in = 'TRUE'
    elif instance.opt_in == 'no':
        opt_in = 'FALSE'

    user = instance.user
    extended_profile = user.extended_profile if hasattr(user, 'extended_profile') else None
    has_hubspot_contact = bool(extended_profile.hubspot_contact_id) if extended_profile else False

    if not has_hubspot_contact:
        user_json = prepare_user_data_for_hubspot_contact_creation(instance.user)
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
        return

    user_json = {
        'properties': {
            'edx_marketing_opt_in': opt_in
        }
    }
    task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)


@receiver(post_save, sender=UserProfile)
def sync_user_profile_with_hubspot(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver that syncs the specific user profile that triggered the signal with hubspot

    Arguments:
        sender: The particular object that triggered the receiver
        instance: Object that contains data regarding the user and their updated profile fields

    Returns:
        None
    """
    updated_fields = getattr(instance, '_updated_fields', {})
    relevant_signal_fields = ['city', 'country', 'language']

    if not any([field in updated_fields for field in relevant_signal_fields]):
        return

    user = instance.user
    extended_profile = user.extended_profile if hasattr(user, 'extended_profile') else None
    has_hubspot_contact = bool(extended_profile.hubspot_contact_id) if extended_profile else False

    if not has_hubspot_contact:
        user_json = prepare_user_data_for_hubspot_contact_creation(user)
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
        return

    if instance.language or instance.country or instance.city:
        user_json = {
            'properties': {
                'edx_language': instance.language or '',
                'edx_country': instance.country.name.format() if instance.country else '',
                'edx_city': instance.city or '',
            }
        }
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)


@receiver(post_save, sender=UserExtendedProfile)
def sync_extended_profile_with_hubspot(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver that syncs the specific user extended profile that triggered the signal with hubspot

    Arguments:
        sender: The particular object that triggered the receiver
        instance: Object that contains data regarding the user

    Returns:
        None
    """
    user = instance.user
    has_hubspot_contact = bool(instance.hubspot_contact_id)

    if not has_hubspot_contact:
        user_json = prepare_user_data_for_hubspot_contact_creation(user)
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
        return

    org_label = org_type = work_area = ''
    if instance.organization:
        org_label, org_type, work_area = instance.organization.hubspot_data()

    user_json = {
        'properties': {
            'edx_organization': org_label,
            'edx_organization_type': org_type,
            'edx_area_of_work': work_area
        }
    }
    task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)


@receiver(post_save, sender=Organization)
def sync_organization_with_hubspot(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    """
    Sync Organization data with HubSpot.
    """
    if not created:
        org_label, org_type, work_area = instance.hubspot_data()
        task_update_org_details_at_hubspot.delay(org_label, org_type, work_area, instance.id)


def send_user_info_to_hubspot(sender, user, created, kwargs):  # pylint: disable=unused-argument
    """
    Create user account on HubSpot when created on Platform.
    """
    extended_profile = user.extended_profile if hasattr(user, 'extended_profile') else None
    has_hubspot_contact = bool(extended_profile.hubspot_contact_id) if extended_profile else False

    if not has_hubspot_contact:
        user_json = prepare_user_data_for_hubspot_contact_creation(user)
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
        return

    user_json = {
        'properties': {
            'edx_full_name': user.get_full_name(),
            'edx_username': user.username
        }
    }

    if created:
        user_json['properties'].update(
            {'date_registered': str(user.date_joined.strftime('%m/%d/%Y'))})
        user_json.update({
            'email': user.email,
            'edx_marketing_opt_in': 'subscribed'
        })

    task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)


def update_user_email_in_hubspot(old_email, new_email):
    """
    Update the email to new_email in hubspot

    Arguments:
        old_email (str): Current email
        new_email (str): Updated email
    """

    user_json = {
        'properties': {
            'email': new_email
        }
    }

    task_create_or_update_hubspot_contact.delay(old_email, user_json, True)


def send_user_enrollments_to_hubspot(user):
    """
    Send all the active enrollments of the specified user to hubspot

    Arguments:
        user: Target user
    """
    extended_profile = user.extended_profile if hasattr(user, 'extended_profile') else None
    has_hubspot_contact = bool(extended_profile.hubspot_contact_id) if extended_profile else False

    if not has_hubspot_contact:
        user_json = prepare_user_data_for_hubspot_contact_creation(user)
        task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
        return

    log.info("-------------------------\n fetching enrollments \n ------------------------------\n")

    enrollment_titles = get_user_active_enrollements(user.username)
    enrollment_short_ids = get_enrollements_course_short_ids(user.username)

    log.info(enrollment_titles)
    log.info(enrollment_short_ids)

    user_json = {
        'properties': {
            'edx_enrollments': enrollment_titles,
            'edx_enrollments_short_ids': enrollment_short_ids
        }
    }

    task_create_or_update_hubspot_contact.delay(user.email, user_json, has_hubspot_contact)
