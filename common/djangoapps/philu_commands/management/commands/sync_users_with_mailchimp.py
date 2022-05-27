"""
A command to collect users data and sync with mailchimp learner's list
"""
from logging import getLogger

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import connection

from lms.djangoapps.certificates import api as certificate_api
from lms.djangoapps.onboarding.models import FocusArea, OrgSector
from mailchimp_pipeline.client import ChimpClient
from mailchimp_pipeline.helpers import get_enrollements_course_short_ids, get_user_active_enrollements
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

log = getLogger(__name__)


class Command(BaseCommand):
    """
    A command to collect users data and sync with mailchimp learner's list
    """

    help = """
    One time addition of already existing users into mailchimp learner's list
    example:
        manage.py sync_users_with_mailchimp
    """

    def send_user_to_mailchimp(self, client, users):
        client.add_list_members_in_batch(settings.MAILCHIMP_LEARNERS_LIST_ID, {
            "members": users,
            "update_existing": True
        })

    def get_users_data_to_send(self, users):
        """
        Get users data to send to mailchimp

        Args:
            users (list): List of user objects

        Returns:
            list: list of dicts with users data
        """
        users_set = []

        focus_areas = FocusArea.get_map()
        org_sectors = OrgSector.objects.get_map()

        for user in users:
            language = country = city = organization = org_type = work_area = ""
            profile = extended_profile = None
            try:
                profile = user.profile
                extended_profile = user.extended_profile

                if profile.language:
                    language = profile.language

                if profile.country:
                    country = profile.country.name.format()

                if profile.city:
                    city = profile.city

                if extended_profile.organization:
                    organization = extended_profile.organization.label
                    work_area = str(focus_areas.get(
                        extended_profile.organization.focus_area, ""
                    ))
                    if extended_profile.organization.org_type:
                        org_type = org_sectors.get(
                            extended_profile.organization.org_type, ''
                        )
            except Exception:  # pylint: disable=broad-except
                log.exception(
                    "User %s does not have related object profile or extended_profile.",
                    user.username
                )

            all_certs = []
            try:
                all_certs = certificate_api.get_certificates_for_user(user.username)
            except Exception as ex:  # pylint: disable=broad-except
                log.exception(str(ex.args))

            completed_course_keys = [cert.get('course_key', '') for cert in all_certs
                                     if certificate_api.is_passing_status(cert['status'])]
            completed_courses = CourseOverview.objects.filter(id__in=completed_course_keys)

            try:
                user_json = {
                    "email_address": user.email,
                    "status_if_new": "subscribed",
                    "merge_fields": {
                        "FULLNAME": user.get_full_name(),
                        "USERNAME": user.username,
                        "LANG": language,
                        "COUNTRY": country,
                        "CITY": city,
                        "DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y")),
                        "LSOURCE": "",
                        "COMPLETES": ", ".join([course.display_name for course in completed_courses]),
                        "ENROLLS": get_user_active_enrollements(user.username),
                        "ENROLL_IDS": get_enrollements_course_short_ids(user.username),
                        "ORG": organization,
                        "ORGTYPE": org_type,
                        "WORKAREA": work_area,
                    }
                }
            except Exception as ex:  # pylint: disable=broad-except
                log.info("There was an error for user with email address as {}".format(user.email))
                log.exception(str(ex.args))
                continue

            users_set.append(user_json)

        return users_set

    def handle(self, *args, **options):
        return

        batch_size = 500
        cursor = connection.cursor()
        cursor.execute('SET TRANSACTION ISOLATION LEVEL READ COMMITTED')
        client = ChimpClient()
        total_user_count = User.objects.all().count()
        page_count = total_user_count / batch_size
        counter = 0

        while counter is not page_count + 1:
            try:
                page_start = counter * batch_size
                page_end = page_start + batch_size
                users = list(User.objects.all()[page_start:page_end])
                log.info(User.objects.all()[page_start:page_end].query)
                users_json = self.get_users_data_to_send(users)
                self.send_user_to_mailchimp(client, users_json)
            except Exception as ex:  # pylint: disable=broad-except
                log.info("There was an error in batch from {} to {}".format(page_start, page_end))
                log.exception(str(ex.args))

            counter += 1
