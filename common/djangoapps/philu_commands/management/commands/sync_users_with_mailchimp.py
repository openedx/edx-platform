import json
from enrollment.api import get_enrollments
from django.core.management.base import BaseCommand
from mailchimp_pipeline.client import ChimpClient
from django.contrib.auth.models import User
from lms.djangoapps.onboarding.models import FocusArea, OrgSector
from lms.djangoapps.certificates import api as certificate_api
from django.conf import settings

from logging import getLogger
log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    One time addition of already existing users into mailchimp learner's list
    example:
        manage.py sync_users_with_mailchimp
    """

    def __int__(self):
        self.list_id = settings.MAILCHIMP_LEARNERS_LIST_ID

    def send_user_to_mailchimp(self, client, users):
        client.add_list_members_in_batch(self.list_id, {"members": users})

    def get_users_data_to_send(self, users):
        users_set = []
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
            except:
                pass

            if user.email == "muhammad.nadeem@arbisoft.com":
                pass

            user_json = {
                "email_address": user.email,
                "status_if_new": "subscribed",
                "merge_fields": {
                    "FULLNAME": user.get_full_name(),
                    "USERNAME": user.username,
                    "LANG": profile.language if profile.language else "",
                    "COUNTRY": profile.country.name.format() if profile.country else "",
                    "CITY": profile.city if profile.city else "",
                    "DATEREGIS": str(user.date_joined.strftime("%m/%d/%Y")),
                    "LSOURCE": "",
                    "COMPLETES": json.dumps([{"course_id": cert.get('course_key', {}).__str__(),
                                            "course_name": cert.get('course_key', {}).course} for cert in all_certs
                                             if certificate_api.is_passing_status(cert['status'])]),
                    "ENROLLS": json.dumps([{"course_id": enrollment.get('course_details', {}).get('course_id', ''),
                                            "course_name": enrollment.get('course_details', {}).get('course_name', '')}
                                           for enrollment in get_enrollments(user.username)]),
                    "ORG": extended_profile.organization.label if extended_profile.organization else "",
                    "ORGTYPE": org_type,
                    "WORKAREA": str(focus_areas.get(extended_profile.organization.focus_area, ""))
                    if extended_profile.organization else "",
                }
            }

            users_set.append(user_json)

        return users_set

    def handle(self, *args, **options):
        batch_size = 500
        client = ChimpClient()

        users = list(User.objects.all())
        for i in xrange(0, len(users), batch_size):
            users_json = self.get_users_data_to_send(users[i:i + batch_size])
            self.send_user_to_mailchimp(client, users_json)

        pass
