"""
Tasks related to the mailchimp_pipeline app
"""
from logging import getLogger

from celery import task
from django.contrib.auth.models import User
from django.db import connection

from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import FocusArea, OrgSector
from mailchimp_pipeline.client import ChimpClient, MailChimpException
from mailchimp_pipeline.helpers import get_enrollements_course_short_ids, get_user_active_enrollements
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = getLogger(__name__)


@task()
def update_enrollments_completions_at_mailchimp(list_id):
    """Task to send user enrollments & course completions details to MailChimp"""
    return

    log.info("starting enrollments & completions sync")

    cursor = connection.cursor()
    cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')

    batch_size = 100
    total_user_count = User.objects.all().count()
    page_count = total_user_count / batch_size
    counter = 0

    while counter is not page_count + 1:
        try:
            page_start = counter * batch_size
            page_end = page_start + batch_size

            users = list(User.objects.all()[page_start:page_end])
            log.info("Syncing batch from {} to {}".format(page_start, page_end))

            focus_areas = FocusArea.get_map()
            org_sectors = OrgSector.objects.get_map()

            for user in users:
                profile = user.profile
                extended_profile = user.extended_profile

                org_type = ""
                if extended_profile.organization and extended_profile.organization.org_type:
                    org_type = org_sectors.get(extended_profile.organization.org_type, '')

                all_certs = []
                try:
                    all_certs = certificate_api.get_certificates_for_user(user.username)
                except Exception as ex:  # pylint: disable=broad-except
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
                    log.info(
                        "Mailchimp-Sync Method: User with email address {} synced successfully".format(user.email)
                    )
                    log.info(response)
                except MailChimpException as ex:
                    log.info(
                        "Mailchimp-Sync Method: "
                        "There was error syncing user with email address {}".format(user.email)
                    )
                    log.exception(ex)

        except Exception as ex:  # pylint: disable=broad-except
            log.info("There was an error in batch from {} to {}".format(page_start, page_end))
            log.exception(str(ex.args))

        counter += 1
