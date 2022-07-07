"""
Handlers for onboarding app
"""
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.db import connection
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from lms.djangoapps.onboarding.constants import NOT_INTERESTED_KEY, REMIND_ME_LATER_KEY, TAKE_ME_THERE_KEY
from lms.djangoapps.onboarding.helpers import (
    its_been_year,
    its_been_year_month,
    its_been_year_six_month,
    its_been_year_three_month,
    update_user_email
)
from lms.djangoapps.onboarding.models import (
    MetricUpdatePromptRecord,
    Organization,
    OrganizationMetric,
    OrganizationMetricUpdatePrompt,
    UserExtendedProfile
)
from oef.models import OrganizationOefUpdatePrompt
from util.model_utils import USER_FIELD_CHANGED, get_changed_fields_dict


@receiver(post_save, sender=User)
def update_user_profile(sender, instance, update_fields, **kwargs):
    user = instance
    user_profile = hasattr(user, 'profile') and user.profile

    # To avoid an extra sync at every login
    if (not update_fields or 'last_login' not in update_fields) and user_profile:
        user_profile.name = '{} {}'.format(user.first_name.encode('utf-8'), user.last_name.encode('utf-8'))
        user_profile.save()


@receiver(post_save, sender=Organization)
def update_responsible_user_to_admin(sender, instance, update_fields, **kwargs):
    if not kwargs['created'] and instance.admin_id:
        try:
            prompt = OrganizationMetricUpdatePrompt.objects.get(org_id=instance.id)
            prompt.responsible_user_id = instance.admin_id
            prompt.save()

            oef_prompt = OrganizationOefUpdatePrompt.objects.get(org_id=instance.id)
            oef_prompt.responsible_user_id = instance.admin_id
            oef_prompt.save()
        except ObjectDoesNotExist:
            pass


@receiver(post_save, sender=OrganizationMetric)
def update_metric_prompts(instance, created, update_fields, **kwargs):
    this_metric_prompts = OrganizationMetricUpdatePrompt.objects.filter(org_id=instance.org_id)

    # Prepare date for prompt against this save in Organization Metric
    submission_date = instance.submission_date
    responsible_user = instance.org.admin or instance.user
    org = instance.org
    latest_metric_submission = instance.submission_date
    year = submission_date and its_been_year(submission_date)
    year_month = submission_date and its_been_year_month(submission_date)
    year_three_month = submission_date and its_been_year_three_month(submission_date)
    year_six_month = submission_date and its_been_year_six_month(submission_date)

    # If prompts against this Metric's already exists, update that prompt
    if len(this_metric_prompts):
        prompt = this_metric_prompts[0]
        prompt.responsible_user = responsible_user
        prompt.latest_metric_submission = latest_metric_submission
        prompt.year = year
        prompt.year_month = year_month
        prompt.year_three_month = year_three_month
        prompt.year_six_month = year_six_month
        prompt.save()
    else:
        # ceate a new prompt and save it
        prompt = OrganizationMetricUpdatePrompt(responsible_user=responsible_user,
                                                org=org,
                                                latest_metric_submission=latest_metric_submission,
                                                year=year,
                                                year_month=year_month,
                                                year_three_month=year_three_month,
                                                year_six_month=year_six_month
                                                )
        prompt.save()


@receiver(post_save, sender=MetricUpdatePromptRecord)
def update_remind_me_later(instance, **kwargs):
    prompt = instance.prompt
    click = str(instance.click)
    if prompt:
        if click == REMIND_ME_LATER_KEY:
            prompt.remind_me_later = True
        elif click == TAKE_ME_THERE_KEY:
            prompt.remind_me_later = None
        elif click == NOT_INTERESTED_KEY:
            prompt.remind_me_later = False
        prompt.save()


@receiver(post_delete, sender=User)
def delete_all_user_data(sender, instance, **kwargs):

    cursor = connection.cursor()

    cursor.execute(
        'UPDATE onboarding_organization SET unclaimed_org_admin_email=NULL WHERE unclaimed_org_admin_email="{}"'.format(instance.email))
    cursor.execute(
        'UPDATE onboarding_organization SET alternate_admin_email=NULL WHERE alternate_admin_email="{}"'.format(instance.email))


@receiver(USER_FIELD_CHANGED)
def propagate_email_change(sender, user=None, table=None, setting=None, old_value=None,
                           new_value=None, **kwargs):
    """
    This method listens for change in user model. Once it detects change in email, it propagate
    change, where required i.e. NodeBB, Mailchimp etc
    :param sender: Not used
    :param user: The user object for the user being changed
    :param table: The name of the table being updated
    :param setting: The name of the field (column) being updated
    :param old_value: Prior value
    :param new_value: New value
    :param kwargs: Not used
    :return: None
    """
    # ignore tables except user and fields except email
    if table != "auth_user" or setting != "email":
        return

    if new_value and new_value != old_value:
        update_user_email(user, old_value, new_value)


@receiver(pre_save, sender=UserExtendedProfile)
def extended_profile_pre_save_callback(sender, **kwargs):
    """
    Capture old fields on the UserExtendedProfile instance before save and cache them as a
    private field on the current model for use in the post_save callback.
    """
    user_extended_profile = kwargs['instance']
    user_extended_profile._changed_fields = get_changed_fields_dict(user_extended_profile, sender)
