from django.core.management.base import BaseCommand, CommandError
from xmodule.contentstore.utils import empty_asset_trashcan
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.keys import CourseKey
from .prompt import query_yes_no


class Command(BaseCommand):
    help = '''Empty the trashcan. Can pass an optional course_id to limit the damage.'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 0:
            raise CommandError("empty_asset_trashcan requires one or no arguments: |<course_id>|")

        if len(args) == 1:
            course_ids = [CourseKey.from_string(args[0])]
        else:
            course_ids = [course.id for course in modulestore('direct').get_courses()]

        if query_yes_no("Emptying trashcan. Confirm?", default="no"):
            empty_asset_trashcan(course_ids)
