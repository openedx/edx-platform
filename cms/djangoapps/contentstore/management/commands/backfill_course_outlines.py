"""
Management command to create the course outline for all courses that are missing
an outline. Outlines are built automatically on course publish and manually
using the `update_course_outline` command, but they can be backfilled using this
command. People updating to Lilac release should run this command as part of the
upgrade process.

This should be invoked from the Studio process.
"""
import logging

from django.core.management.base import BaseCommand

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.content.learning_sequences.api import (
    get_course_keys_with_outlines,
    key_supports_outlines,
)

from ...tasks import update_outline_from_modulestore_task

log = logging.getLogger('backfill_course_outlines')


class Command(BaseCommand):
    """
    Invoke with:

        python manage.py cms backfill_course_outlines
    """
    help = (
        "Backfill missing course outlines. This will queue a celery task for "
        "each course with a missing outline, meaning that the outlines may be "
        "generated minutes or hours after this script has finished running."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry',
            action='store_true',
            help="Show course outlines that will be backfilled, but do not make any changes."
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry', False)
        log.info("Starting backfill_course_outlines{}".format(" (dry run)" if dry_run else ""))

        all_course_keys_qs = CourseOverview.objects.values_list('id', flat=True)
        # .difference() is not supported in MySQL, but this at least does the
        # SELECT NOT IN... subquery in the database rather than Python.
        missing_outlines_qs = all_course_keys_qs.exclude(
            id__in=get_course_keys_with_outlines()
        )
        num_courses_needing_outlines = len(missing_outlines_qs)
        log.info(
            "Found %d courses without outlines. Queuing tasks...",
            num_courses_needing_outlines
        )

        for course_key in missing_outlines_qs:
            if key_supports_outlines(course_key):
                log.info("Queuing outline creation for %s", course_key)
                if not dry_run:
                    update_outline_from_modulestore_task.delay(str(course_key))
            else:
                log.info("Outlines not supported for %s - skipping", course_key)
