from celery import task
from django.contrib.auth.models import User
from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import (UserExtendedProfile,FocusArea, OrgSector, )
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.helpers import get_user_active_enrollements, get_enrollements_course_short_ids

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
    users = User.objects.all()

    for user in users:
        profile = user.profile
        extended_profile = user.extended_profile

        focus_areas = FocusArea.get_map()
        org_sectors = OrgSector.get_map()

        org_type = ""
        if extended_profile.organization and extended_profile.organization.org_type:
            org_type = org_sectors.get(extended_profile.organization.org_type, '')

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
                "FULLNAME": user.get_full_name(),
                "USERNAME": user.username,
                "LANG": profile.language if profile.language else "",
                "COUNTRY": profile.country.name.format() if profile.country else "",
                "CITY": profile.city if profile.city else "",
                "DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y")),
                "LSOURCE": "",
                "ENROLLS": get_user_active_enrollements(user.username),
                "ENROLL_IDS": get_enrollements_course_short_ids(user.username),
                "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
                "ORG": extended_profile.organization.label if extended_profile.organization else "",
                "ORGTYPE": org_type,
                "WORKAREA": str(focus_areas.get(extended_profile.organization.focus_area, ""))
                if extended_profile.organization else "",
            }
        }
        try:
            response = ChimpClient().add_update_member_to_list(list_id, user.email, user_json)
            log.info(response)
        except MailChimpException as ex:
            log.exception(ex)
