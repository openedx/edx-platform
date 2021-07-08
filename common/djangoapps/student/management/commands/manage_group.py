"""
Management command `manage_group` is used to idempotently create Django groups
and set their permissions by name.
"""


from edx_django_utils.management.user.manage_group import manage_group
from django.utils.translation import gettext as _


class Command(BaseCommand):  # lint-amnesty, pylint: disable=missing-class-docstring
    help = 'Creates the specified group, if it does not exist, and sets its permissions.'

    def add_arguments(self, parser):
        parser.add_argument('group_name')
        parser.add_argument('--remove', dest='is_remove', action='store_true')
        parser.add_argument('-p', '--permissions', nargs='*', default=[])

    def handle(self, group_name, is_remove, permissions=None, *args, **options):  # lint-amnesty, pylint: disable=arguments-differ, keyword-arg-before-vararg
        manage_group(group_name, is_remove, permissions=None, *args, **options)
