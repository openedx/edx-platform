"""
Reload forum (comment client) users from existing users.
"""
from __future__ import print_function

import lms.lib.comment_client as cc
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Reload forum (comment client) users from existing users.'

    def add_arguments(self, parser):
        parser.add_argument('usernames',
                            nargs='*',
                            metavar='username',
                            help='zero or more usernames (zero implies all users)')

    def adduser(self, user):
        print(user)
        try:
            cc_user = cc.User.from_django_user(user)
            cc_user.save()
        except Exception as err:
            print('update user info to discussion failed for user with id: {}, error={}'.format(user, str(err)))

    def handle(self, *args, **options):
        if len(options['usernames']) >= 1:
            user_list = User.objects.filter(username__in=options['usernames'])
        else:
            user_list = User.objects.all()

        for user in user_list:
            self.adduser(user)
