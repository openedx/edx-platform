from django.core.management.base import BaseCommand, CommandError
from xmodule.contentstore.utils import empty_asset_trashcan
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.keys import CourseKey
from .prompt import query_yes_no
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locations import SlashSeparatedCourseKey


class Command(BaseCommand):
    help = '''Empty the trashcan. Can pass an optional course_id to limit the damage.'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 0:
            raise CommandError("empty_asset_trashcan requires one or no arguments: |<course_id>|")

        if len(args) == 1:
            try:
                course_key = CourseKey.from_string(args[0])
            except InvalidKeyError:
                course_key = SlashSeparatedCourseKey.from_deprecated_string(args[0])

            course_ids = [course_key]
        else:
            course_ids = [course.id for course in modulestore().get_courses()]

        if query_yes_no("Emptying trashcan. Confirm?", default="no"):
            empty_asset_trashcan(course_ids)
