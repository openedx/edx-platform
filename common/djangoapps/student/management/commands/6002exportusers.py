##
## One-off script to export 6.002x users into the edX framework
##
## Could be modified to be general by:
## * Changing user_keys and up_keys to handle dates more cleanly
## * Providing a generic set of tables, rather than just users and user profiles
## * Handling certificates and grades
## * Handling merge/forks of UserProfile.meta


import datetime
import json

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from student.models import UserProfile


class Command(BaseCommand):
    help = """Exports all users and user profiles.
Caveat: Should be looked over before any run
for schema changes.

Current version grabs user_keys from
django.contrib.auth.models.User and up_keys
from student.userprofile."""

    def handle(self, *args, **options):
        users = list(User.objects.all())
        user_profiles = list(UserProfile.objects.all())
        user_profile_dict = dict([(up.user_id, up) for up in user_profiles])

        user_tuples = [(user_profile_dict[u.id], u) for u in users if u.id in user_profile_dict]

        user_keys = ['id', 'username', 'email', 'password', 'is_staff',
                     'is_active', 'is_superuser', 'last_login', 'date_joined',
                     'password']
        up_keys = ['language', 'location', 'meta', 'name', 'id', 'user_id']

        def extract_dict(keys, object):
            d = {}
            for key in keys:
                item = object.__getattribute__(key)
                if type(item) == datetime.datetime:
                    item = item.isoformat()
                d[key] = item
            return d

        extracted = [{'up': extract_dict(up_keys, t[0]), 'u':extract_dict(user_keys, t[1])} for t in user_tuples]
        fp = open('transfer_users.txt', 'w')
        json.dump(extracted, fp)
        fp.close()
