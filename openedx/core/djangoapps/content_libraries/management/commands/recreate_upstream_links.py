"""
Management command to recreate upstream-dowstream links in PublishableEntityLink for course(s).

This command can be run for all the courses or for given list of courses.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import gettext as _

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview

from ...tasks import create_or_update_upstream_links

log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Recreate links for course(s) in PublishableEntityLink table.

    Examples:
        # Recreate upstream links for two courses.
        $ ./manage.py cms recreate_upstream_links --course course-v1:edX+DemoX.1+2014 \
        --course course-v1:edX+DemoX.2+2015
        # Recreate upstream links for all courses.
        $ ./manage.py cms recreate_upstream_links --all
        # Force recreate links for all courses including completely processed ones.
        $ ./manage.py cms recreate_upstream_links --all
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--course',
            metavar=_('COURSE_KEY'),
            action='append',
            help=_('Recreate links for xblocks under given course keys. For eg. course-v1:edX+DemoX.1+2014'),
            default=[],
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help=_(
                'Recreate links for xblocks under all courses. NOTE: this can take long time depending'
                ' on number of course and xblocks'
            ),
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help=_('Recreate links even for completely processed courses.'),
        )

    def handle(self, *args, **options):
        """
        Handle command
        """
        courses = options['course']
        should_process_all = options['all']
        force = options['force']
        self.time_now = datetime.now(tz=timezone.utc)
        if not courses and not should_process_all:
            raise CommandError('Either --course or --all argument should be provided.')

        if should_process_all and courses:
            raise CommandError('Only one of --course or --all argument should be provided.')

        if should_process_all:
            courses = CourseOverview.get_all_course_keys()
        for course in courses:
            create_or_update_upstream_links.delay(str(course), force)
