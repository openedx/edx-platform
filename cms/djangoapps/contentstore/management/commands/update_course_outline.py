"""
Management command to create the course outline for a course. This is done
automatically when Studio publishes a course, but this command can be used to
do it manually for debugging, error recovery, or backfilling purposes.

Should be invoked from the Studio process.
"""
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from ...tasks import update_outline_from_modulestore


class Command(BaseCommand):
    """
    Invoke with:

        python manage.py cms update_course_outline <course_key>
    """
    help = "Updates a single course outline based on modulestore content."

    def add_arguments(self, parser):
        parser.add_argument('course_key')

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options['course_key'])
        update_outline_from_modulestore(course_key)
