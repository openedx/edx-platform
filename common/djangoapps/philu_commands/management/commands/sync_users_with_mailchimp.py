from django.core.management.base import BaseCommand
from lms.djangoapps.mailchimp_pipeline.client import ChimpClient
from django.contrib.auth.models import User

from logging import getLogger
log = getLogger(__name__)

list_id = "885da93a66"


class Command(BaseCommand):
    help = """
    One time addition of already existing users into mailchimp learner's list
    example:
        manage.py sync_users_with_mailchimp
    """

    def send_user_to_mailchimp(self, client, users):
        client.add_list_members_in_batch(list_id, {"members": users})

    def get_users_data_to_send(self, users):
        users_set = []
        for user in users:
            profile = user.profile
            extended_profile = user.extended_profile
            org_type = ""
            if extended_profile.organization and extended_profile.organization.org_type:
                org_type = extended_profile.organization.org_type

            user_json = {
                "email_address": user.email,
                "status_if_new": "subscribed",
                "merge_fields": {
                    "FULLNAME": user.get_full_name(),
                    "USERNAME": user.username,
                    "LANG": profile.language if profile.language else "",
                    "COUNTRY": profile.country.name.format() if profile.country else "",
                    "CITY": profile.city if profile.city else "",
                    "DATER": user.date_joined.strftime("%m/%d/%Y"),
                    "LSOURCE": "",
                    "COMPLETES": "",
                    "ENROLLS": "",
                    "ORG": extended_profile.organization.label if extended_profile.organization else "",
                    "ORGTYPE": org_type,
                    "WORKAREA": "",
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
