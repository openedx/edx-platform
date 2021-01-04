# pylint: disable=missing-module-docstring,too-many-format-args


from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show a user's roles and permissions."

    def add_arguments(self, parser):
        parser.add_argument('email_or_username',
                            help='the email or username of the user')

    def handle(self, *args, **options):
        email_or_username = options['email_or_username']
        try:
            if '@' in email_or_username:
                user = User.objects.get(email=email_or_username)
            else:
                user = User.objects.get(username=email_or_username)
        except User.DoesNotExist:
            print(u'User {} does not exist. '.format(email_or_username))
            print('Available users: ')
            print(User.objects.all())
            return

        roles = user.roles.all()
        print(u'{} has %d roles:'.format(user, len(roles)))
        for role in roles:
            print(u'\t{}'.format(role))

        for role in roles:
            print(u'{} has permissions: '.format(role))
            print(role.permissions.all())
