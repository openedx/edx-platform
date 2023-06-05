from django.core.management.base import BaseCommand, CommandError

from opaque_keys.edx.keys import CourseKey

from ...tasks import update_from_modulestore


class Command(BaseCommand):
    help = "Updates a single course outline based on modulestore content."

    def add_arguments(self, parser):
        parser.add_argument('course_key')

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options['course_key'])
        update_from_modulestore(course_key)
