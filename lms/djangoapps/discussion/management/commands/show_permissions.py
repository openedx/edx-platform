# pylint: disable=missing-module-docstring,too-many-format-args


from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.management.base import BaseCommand
from django.db.models import Q


class Command(BaseCommand):  # lint-amnesty, pylint: disable=missing-class-docstring
    help = "Show a user's roles and permissions."

    def add_arguments(self, parser):
        parser.add_argument('email_or_username',
                            help='the email or username of the user')

    def handle(self, *args, **options):
        email_or_username = options['email_or_username']
        user = User.objects.filter(Q(username=email_or_username) | Q(email=email_or_username)).first()
        if not user:
            print('User {} does not exist. '.format(email_or_username))
            print('Available users: ')
            print(User.objects.all())
            return

        roles = user.roles.all()
        print(u'{} has {} roles:'.format(user, len(roles)))
        for role in roles:
            print(u'\t{}'.format(role))

        for role in roles:
            print(u'{} has permissions: '.format(role))
            print(role.permissions.all())
