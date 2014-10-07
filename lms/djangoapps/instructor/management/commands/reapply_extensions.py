#!/usr/bin/python
from django.http import Http404
from django.core.management.base import BaseCommand, CommandError, make_option

from courseware.courses import get_course_by_id
from instructor.views.tools import reapply_all_extensions


class Command(BaseCommand):
    args = "<course_id>"
    help = "Reapply all extensions (fixes extensions for newly added problems)"
    option_list = BaseCommand.option_list + (
        make_option('--dry-run',
                    dest='dry_run',
                    action='store_true',
                    default=False,
                    help='Show what would be done without actually doing '
                    'anything'),
    )

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError("insufficient arguments")
        try:
            course = get_course_by_id(args[0])
            reapply_all_extensions(course, dry_run=options['dry_run'])
        except (ValueError, Http404) as e:
            raise CommandError(e)
