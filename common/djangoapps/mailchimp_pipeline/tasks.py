from celery import task
from enrollment.api import get_enrollments
from django.contrib.auth.models import User
from django.contrib.sessions.backends.db import SessionStore
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import UserExtendedProfile
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.helpers import is_active_enrollment

from logging import getLogger
log = getLogger(__name__)


@task()
def update_org_details_at_mailchimp(org_label, org_type, work_area, list_id):
    log.info("Task to send organization details to MailChimp")
    log.info(org_label)

    extended_profiles = UserExtendedProfile.objects.filter(organization__label__iexact=org_label.lower()).values("user__email")

    for extended_profile in extended_profiles:
        user_json = {
            "merge_fields": {
                "ORG": org_label,
                "ORGTYPE": org_type,
                "WORKAREA": work_area
            }
        }
        try:
            response = ChimpClient().add_update_member_to_list(list_id, extended_profile.get('user__email'), user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)


@task()
def update_enrollments_completions_at_mailchimp(list_id):
    """Task to send user enrollments & course completions details to MailChimp"""
    log.info("starting enrollments & completions sync")
    users = User.objects.values("username", "email")

    for user in users:
        all_certs = []
        try:
            all_certs = certificate_api.get_certificates_for_user(user["username"])
        except Exception as ex:
            log.exception(str(ex.args))

        user_json = {
            "merge_fields": {
                "ENROLLS": ", ".join([enrollment.get('course_details', {}).get('course_name', '')
                          for enrollment in get_enrollments(user["username"])
                          if is_active_enrollment(enrollment.get('course_details', {}).get('course_end', ''))]),
                "COMPLETES": ", ".join([cert.get('course_key', {}).course for cert in all_certs
                                        if certificate_api.is_passing_status(cert['status'])]),
            }
        }
        try:
            response = ChimpClient().add_update_member_to_list(list_id, user["email"], user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)
