from enrollment.api import get_enrollments
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.helpers import get_org_data_for_mandrill, is_active_enrollment
from mailchimp_pipeline.tasks import update_org_details_at_mailchimp
from lms.djangoapps.onboarding.models import (UserExtendedProfile, Organization, EmailPreference,)
from lms.djangoapps.certificates import api as certificate_api
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from student.models import (UserProfile, CourseEnrollment, )
from django.conf import settings

from logging import getLogger
log = getLogger(__name__)


def send_user_profile_info_to_mailchimp(sender, instance, kwargs):  # pylint: disable=unused-argument, invalid-name
    """ Create user account at nodeBB when user created at edx Platform """
    user_json = None
    if sender == UserProfile:
        profile = instance
        user_json = {
            "merge_fields": {
                "LANG": profile.language if profile.language else "",
                "COUNTRY": profile.country.name.format() if profile.country else "",
                "CITY": profile.city if profile.city else "",
            }
        }
    elif sender == UserExtendedProfile:
        extended_profile = instance
        org_label, org_type, work_area = get_org_data_for_mandrill(extended_profile.organization)
        user_json = {
            "merge_fields": {
                "ORG": org_label,
                "ORGTYPE": org_type,
                "WORKAREA": work_area
            }
        }
    elif sender == EmailPreference:
        email_preferences = instance

        if email_preferences.opt_in == 'yes':
            opt_in = 'TRUE'
        elif email_preferences.opt_in == 'no':
            opt_in = 'FALSE'
        else:
            opt_in = ''
        user_json = {
            "merge_fields": {
                "OPTIN": opt_in
            }
        }

    elif sender == Organization:
        org_label, org_type, work_area = get_org_data_for_mandrill(instance)
        update_org_details_at_mailchimp.delay(org_label, org_type, work_area, settings.MAILCHIMP_LEARNERS_LIST_ID)

    if user_json and not sender == Organization:
        try:
            response = ChimpClient().add_update_member_to_list(settings.MAILCHIMP_LEARNERS_LIST_ID, instance.user.email, user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)


def send_user_info_to_mailchimp(sender, user, created, kwargs):
    """ Create user account at nodeBB when user created at edx Platform """

    user_json = {
        "merge_fields": {
            "FULLNAME": user.get_full_name(),
            "USERNAME": user.username
        }
    }

    if created:
        user_json["merge_fields"].update({"DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y"))})
        user_json.update({
            "email_address": user.email,
            "status_if_new": "subscribed"
        })
    try:
        response = ChimpClient().add_update_member_to_list(settings.MAILCHIMP_LEARNERS_LIST_ID, user.email, user_json)
        log.info(response)
    except MailChimpException as ex:
        log.exception(ex)


def send_user_enrollments_to_mailchimp(sender, instance, created, kwargs):
    user_json = {
        "merge_fields": {
            "ENROLLS": ", ".join([enrollment.get('course_details', {}).get('course_name', '')
                                  for enrollment in get_enrollments(instance.user.username)
                                  if is_active_enrollment(enrollment.get('course_details', {}).get('course_end', ''))]),
        }
    }
    try:
        response = ChimpClient().add_update_member_to_list(settings.MAILCHIMP_LEARNERS_LIST_ID, instance.user.email,
                                                           user_json)
        log.info(response)
    except MailChimpException as ex:
        log.exception(ex)


def send_user_course_completions_to_mailchimp(sender, user, course_key, kwargs):
    all_certs = []
    try:
        all_certs = certificate_api.get_certificates_for_user(user.username)
    except Exception as ex:
        log.exception(str(ex.args))

    completed_course_keys = [cert.get('course_key', '') for cert in all_certs
                             if certificate_api.is_passing_status(cert['status'])]
    completed_courses = CourseOverview.objects.filter(id__in=completed_course_keys)
    user_json = {
        "merge_fields": {
            "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
        }
    }
    try:
        response = ChimpClient().add_update_member_to_list(settings.MAILCHIMP_LEARNERS_LIST_ID, user.email, user_json)
        log.info(response)
    except MailChimpException as ex:
        log.exception(ex)
