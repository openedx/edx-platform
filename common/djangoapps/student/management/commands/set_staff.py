from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import re


class Command(BaseCommand):
    args = '<user|email> [user|email ...]>'
    help = """
        This command will set is_staff to true for one or more users.
        Lookup by username or email address, assumes usernames
        do not look like email addresses.
        """

    def add_arguments(self, parser):
        parser.add_argument('--unset',
                            action='store_true',
                            dest='unset',
                            default=False,
                            help='Set is_staff to False instead of True')

    def handle(self, *args, **options):
        if len(args) < 1:
            raise CommandError('Usage is set_staff {0}'.format(self.args))

        for user in args:
            if re.match(r'[^@]+@[^@]+\.[^@]+', user):
                try:
                    v = User.objects.get(email=user)
                except User.DoesNotExist:
                    raise CommandError("User {0} does not exist".format(user))
            else:
                try:
                    v = User.objects.get(username=user)
                except User.DoesNotExist:
                    raise CommandError("User {0} does not exist".format(user))

            if options['unset']:
                v.is_staff = False
            else:
                v.is_staff = True

            v.save()

        print 'Success!'
