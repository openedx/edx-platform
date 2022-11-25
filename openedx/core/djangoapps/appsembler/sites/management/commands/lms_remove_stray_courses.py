"""
Remove stray courses from LMS.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from ...deletion_utils import remove_stray_courses_from_mysql


class Command(BaseCommand):
    """
    Bulk removal of courses without an organization linked (aka stray courses).

    This only works for MySQL database.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            help='Max courses to delete, use 0 to delete all courses.',
            default=1,
            type=int,
        )

        parser.add_argument(
            '--commit',
            help='Otherwise, the transaction would be rolled back.',
            action='store_true',
            dest='commit',
        )

        parser.add_argument(
            '--dry-run',
            help='Dry run the deletion process without removing the courses.',
            action='store_false',
            dest='commit',
        )

    def handle(self, *args, **options):
        if settings.ROOT_URLCONF != 'lms.urls':
            raise CommandError('This command can only be run in LMS.')

        remove_stray_courses_from_mysql(
            limit=options['limit'],
            commit=options.get('commit'),
            print_func=self.stdout.write,
        )
