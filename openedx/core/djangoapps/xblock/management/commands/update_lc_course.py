from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from ...api import update_learning_core_course

class Command(BaseCommand):
    """
    Invoke with:

        python manage.py cms update_lc_course <course_key>
    """
    help = "Updates a single course to read from a hybrid LC/Modulestore interface."

    def add_arguments(self, parser):
        parser.add_argument('course_key')

    def handle(self, *args, **options):
        course_key = CourseKey.from_string(options['course_key'])
        update_learning_core_course(course_key)
