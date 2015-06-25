##
## One-off script to import 6.002x users into the edX framework
## See export for more info


import json

import dateutil.parser

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from student.models import UserProfile


def import_user(u):
    user_info = u['u']
    up_info = u['up']

    # HACK to handle dates
    user_info['last_login'] = dateutil.parser.parse(user_info['last_login'])
    user_info['date_joined'] = dateutil.parser.parse(user_info['date_joined'])

    user_keys = ['id', 'username', 'email', 'password', 'is_staff',
                 'is_active', 'is_superuser', 'last_login', 'date_joined',
                 'password']
    up_keys = ['language', 'location', 'meta', 'name', 'id', 'user_id']

    u = User()
    for key in user_keys:
        u.__setattr__(key, user_info[key])
    u.save()

    up = UserProfile()
    up.user = u
    for key in up_keys:
        up.__setattr__(key, up_info[key])
    up.save()


class Command(BaseCommand):
    help = """Exports all users and user profiles.
Caveat: Should be looked over before any run
for schema changes.

Current version grabs user_keys from
django.contrib.auth.models.User and up_keys
from student.userprofile."""

    def handle(self, *args, **options):
        extracted = json.load(open('transfer_users.txt'))
        n = 0
        for u in extracted:
            import_user(u)
            if n % 100 == 0:
                print n
            n = n + 1
