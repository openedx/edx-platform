"""
Management command `manage_user` is used to idempotently create or remove
Django users, set/unset permission bits, and associate groups by name.
"""

from django.core.management.base import BaseCommand, CommandError
from edx_django_utils.management.user.manage_user import manage_user

# from django.db import transaction
# from django.utils.translation import gettext as _


class Command(BaseCommand):  # lint-amnesty, pylint: disable=missing-class-docstring
    help = 'Creates the specified user, if it does not exist, and sets its groups.'


    def _maybe_update(self, user, attribute, new_value):
        """
        DRY helper.  If the specified attribute of the user differs from the
        specified value, it will be updated.
        """
        old_value = getattr(user, attribute)
        if new_value != old_value:
            self.stderr.write(
                _('Setting {attribute} for user "{username}" to "{new_value}"').format(
                    attribute=attribute, username=user.username, new_value=new_value
                )
            )
            setattr(user, attribute, new_value)

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('email')
        parser.add_argument('--remove', dest='is_remove', action='store_true')
        parser.add_argument('--superuser', dest='is_superuser', action='store_true')
        parser.add_argument('--staff', dest='is_staff', action='store_true')
        parser.add_argument('--unusable-password', dest='unusable_password', action='store_true')
        parser.add_argument('--initial-password-hash', dest='initial_password_hash')
        parser.add_argument('-g', '--groups', nargs='*', default=[])

    def handle(self, username, email, is_remove, is_staff, is_superuser, groups,  # lint-amnesty, pylint: disable=arguments-differ
               unusable_password, initial_password_hash, *args, **options):
        manage_user(self, username, email, is_remove, is_staff, is_superuser, groups,  # lint-amnesty, pylint: disable=arguments-differ
            unusable_password, initial_password_hash, *args, **options)
