"""
Handlers and signals for Mailchimp pipeline
"""
from logging import getLogger

from celery.task import task
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from common.lib.mandrill_client.client import MandrillClient
from common.lib.hubspot_client.client import HubSpotClient
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import EmailPreference, GranteeOptIn, Organization, UserExtendedProfile
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.helpers import (
    get_enrollements_course_short_ids,
    get_org_data_for_mandrill,
    get_user_active_enrollements
)
from mailchimp_pipeline.tasks import update_org_details_at_mailchimp
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import UserProfile

log = getLogger(__name__)


def update_mailchimp(email, data):
    return
    try:
        response = ChimpClient().add_update_member_to_list(
            settings.MAILCHIMP_LEARNERS_LIST_ID, email, data)
        log.info(response)
    except MailChimpException as ex:
        log.exception(ex)


@receiver(post_save, sender=EmailPreference)
def sync_email_preference_with_mailchimp(sender, instance, **kwargs):  # pylint: disable=unused-argument
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

    user_json = {
        "merge_fields": {
            "OPTIN": opt_in
        }
    }

    update_mailchimp(instance.user.email, user_json)


@receiver(post_save, sender=UserProfile)
def sync_user_profile_with_mailchimp(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver that syncs the specific user profile that triggered the signal with mailchimp

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

    if instance.language or instance.country or instance.city:
        user_json = {
            "merge_fields": {
                "LANG": instance.language or "",
                "COUNTRY": instance.country.name.format() if instance.country else "",
                "CITY": instance.city or "",
            }
        }

        update_mailchimp(instance.user.email, user_json)


@receiver(post_save, sender=UserExtendedProfile)
def sync_extended_profile_with_mailchimp(sender, instance, **kwargs):  # pylint: disable=unused-argument
    """
    Signal receiver that syncs the specific user extended profile that triggered the signal with mailchimp

    Arguments:
        sender: The particular object that triggered the receiver
        instance: Object that contains data regarding the user

    Returns:
        None
    """
    org_label, org_type, work_area = get_org_data_for_mandrill(
        instance.organization)

    user_json = {
        "merge_fields": {
            "ORG": org_label,
            "ORGTYPE": org_type,
            "WORKAREA": work_area
        }
    }

    update_mailchimp(instance.user.email, user_json)


@receiver(post_save, sender=GranteeOptIn)
def sync_grantee_optin_with_mailchimp(sender, instance, **kwargs):  # pylint: disable=unused-argument
    if instance.organization_partner.partner == 'ECHIDNA':
        user_json = {
            "merge_fields": {
                "ECHIDNA": 'TRUE' if instance.agreed else 'FALSE',
            }
        }
        update_mailchimp(instance.user.email, user_json)


@receiver(post_save, sender=Organization)
def sync_organization_with_mailchimp(sender, instance, created, **kwargs):  # pylint: disable=unused-argument
    if not created:
        org_label, org_type, work_area = get_org_data_for_mandrill(instance)
        update_org_details_at_mailchimp.delay(
            org_label, org_type, work_area, instance.id, settings.MAILCHIMP_LEARNERS_LIST_ID)


def sync_metric_update_prompt_with_mail_chimp(update_prompt):
    """
    Syncs a specific user's preference regarding the update prompt with mailchimp

    Arguments:
        update_prompt: Object containing details regarding the user and their choice of prompt update

    Returns:
        None
    """
    year = 'TRUE' if update_prompt.year else 'FALSE'
    year_month = 'TRUE' if update_prompt.year_month else 'FALSE'
    year_three_months = 'TRUE' if update_prompt.year_three_month else 'FALSE'
    year_six_months = 'TRUE' if update_prompt.year_six_month else 'FALSE'

    user_json = {
        "merge_fields": {
            "YEAR": year,
            "Y_MONTH": year_month,
            "Y_3MONTHS": year_three_months,
            "Y_6MONTHS": year_six_months
        }
    }

    update_mailchimp(update_prompt.responsible_user.email, user_json)


def send_user_info_to_mailchimp(sender, user, created, kwargs):  # pylint: disable=unused-argument
    """ Create user account at nodeBB when user created at edx Platform """

    user_json = {
        "merge_fields": {
            "FULLNAME": user.get_full_name(),
            "USERNAME": user.username
        }
    }

    if created:
        user_json["merge_fields"].update(
            {"DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y"))})
        user_json.update({
            "email_address": user.email,
            "status_if_new": "subscribed"
        })

    update_mailchimp(user.email, user_json)


def update_user_email_in_mailchimp(old_email, new_email):
    """
    Update the email to new_email in mailchimp

    Arguments:
        old_email (str): Current email
        new_email (str): Updated email

    Returns:
        None
    """

    user_json = {
        "email_address": new_email,
    }

    update_mailchimp(old_email, user_json)


@task(routing_key=settings.HIGH_PRIORITY_QUEUE)
def task_send_account_activation_email(data):
    """
    Task that sends the account activation email containing the given data

    Arguments:
        data: Object containing the details for the activation email

    Returns:
        None
    """
    context = {
        'emailId': HubSpotClient.ACCOUNT_ACTIVATION_EMAIL,
        'message': {
            'to': data['user_email']
        },
        'customProperties': {
            'first_name': data['first_name'],
            'activation_link': data['activation_link'],
        }
    }

    HubSpotClient().send_mail(context)


@task()
def task_send_user_info_to_mailchimp(data):
    """ Create user account at nodeBB when user created at edx Platform """

    user = User.objects.get(id=data['user_id'])
    created = data["created"]

    send_user_info_to_mailchimp(None, user, created, {})


# @task()
def send_user_enrollments_to_mailchimp(user):
    """
    Send all the active enrollments of the specified user to mailchimp

    Arguments:
        user: Target user

    Returns:
        None
    """
    # user = User.objects.get(id=data['user_id'])

    log.info("-------------------------\n fetching enrollments \n ------------------------------\n")

    enrollment_titles = get_user_active_enrollements(user.username)
    enrollment_short_ids = get_enrollements_course_short_ids(user.username)

    log.info(enrollment_titles)
    log.info(enrollment_short_ids)

    user_json = {
        "merge_fields": {
            "ENROLLS": enrollment_titles,
            "ENROLL_IDS": enrollment_short_ids
        }
    }

    update_mailchimp(user.email, user_json)


@task()
def send_user_course_completions_to_mailchimp(data):
    """
    Task to send all the completed courses of a user to mailchimp

    Arguments:
        data: Object containing user info eg user_id

    Returns:
        None
    """
    user = User.objects.get(id=data['user_id'])
    all_certs = []
    try:
        all_certs = certificate_api.get_certificates_for_user(user.username)
    except Exception as ex:  # pylint: disable=broad-except
        log.exception(str(ex.args))

    completed_course_keys = [cert.get('course_key', '') for cert in all_certs
                             if certificate_api.is_passing_status(cert['status'])]
    completed_courses = CourseOverview.objects.filter(
        id__in=completed_course_keys)
    user_json = {
        "merge_fields": {
            "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
        }
    }
    update_mailchimp(user.email, user_json)
