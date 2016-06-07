"""
Reload forum (comment client) users from existing users.
"""
from django.core.management.base import BaseCommand

from django.contrib.auth.models import User
import lms.lib.comment_client as cc


class Command(BaseCommand):
    help = 'Reload forum (comment client) users from existing users'

    def adduser(self, user):
        print user
        try:
            cc_user = cc.User.from_django_user(user)
            cc_user.save()
        except Exception as err:
            print "update user info to discussion failed for user with id: %s, error=%s" % (user, str(err))

    def handle(self, *args, **options):
        if len(args) != 0:
            uset = [User.objects.get(username=x) for x in args]
        else:
            uset = User.objects.all()

        for user in uset:
            self.adduser(user)
