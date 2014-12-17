##
## One-off script to import 6.002x users into the edX framework
## See export for more info

## Hack to CEC EP

import os.path
import json
from optparse import make_option

import dateutil.parser

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from student.models import UserProfile

from cities.models import City


def import_user(u):
    user_info = u['u']
    up_info = u['up']

    # HACK to handle dates
    user_info['last_login'] = dateutil.parser.parse(user_info['last_login'])
    user_info['date_joined'] = dateutil.parser.parse(user_info['date_joined'])

    user_keys = ["id","username","email","password","is_staff","is_active",
                "is_superuser","last_login", "date_joined"]

    up_keys = ["id","user_id","name","cedula","year_of_birth",
               "gender","level_of_education","city", "country"]

#    user_keys = ['id', 'username', 'email', 'password', 'is_staff',
#                 'is_active', 'is_superuser', 'last_login', 'date_joined',
#                 'password']

#    up_keys = ['id', 'user_id', 'name', 'year_of_birth', 'gender',
#               'level_of_education', 'city', 'country']

    u = User()
    for key in user_keys:
        u.__setattr__(key, user_info[key])
    # need to be explicit ?
    u.is_staff = False
    u.is_superuser = False
    u.save()

    up = UserProfile()
    up.user = u
    for key in up_keys:
        valor = up_info[key]
        if key == 'city':
            city = City.objects.get(name__iexact=up_info[key])
            valor = city
        up.__setattr__(key, valor)
    up.year_of_birth = False
    up.save()


class Command(BaseCommand):
    help = """Exports all users and user profiles.
Caveat: Should be looked over before any run
for schema changes.

Current version grabs user_keys from
django.contrib.auth.models.User and up_keys
from student.userprofile."""

    option_list = BaseCommand.option_list + (
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=None,
                    help='Course to enroll all users in file'),
        make_option('-f', '--file',
                    metavar='FILE_PATH',
                    dest='file_path',
                    default='users.txt',
                    help='Fle with all info about users'),
        )

    def handle(self, *args, **options):
        if options['file_path']:
            if not os.path.exists(options['file_path']):
                return
        extracted = json.load(open(options['file_path']))
        n = 0
        for u in extracted:
            import_user(u)
            if n % 100 == 0:
                print n
            n = n + 1
