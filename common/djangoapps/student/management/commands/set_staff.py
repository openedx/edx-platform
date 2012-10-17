from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import re


class Command(BaseCommand):

    args = '<user/email user/email ...>'
    help = """
    This command will set isstaff to true for one or more users.
    Lookup by username or email address, assumes usernames
    do not look like email addresses.
    """

    def handle(self, *args, **kwargs):

        if len(args) < 1:
            print Command.help
            return

        for user in args:

            if re.match('[^@]+@[^@]+\.[^@]+', user):
                try:
                    v = User.objects.get(email=user)
                except:
                    raise CommandError("User {0} does not exist".format(
                        user))
            else:
                try:
                    v = User.objects.get(username=user)
                except:
                    raise CommandError("User {0} does not exist".format(
                        user))

            v.is_staff = True
            v.save()
