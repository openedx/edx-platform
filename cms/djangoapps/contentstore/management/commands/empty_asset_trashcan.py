from django.core.management.base import BaseCommand, CommandError
from xmodule.course_module import CourseDescriptor
from xmodule.contentstore.utils import empty_asset_trashcan
from xmodule.modulestore.django import modulestore
from .prompt import query_yes_no


class Command(BaseCommand):
    help = '''Empty the trashcan. Can pass an optional course_id to limit the damage.'''

    def handle(self, *args, **options):
        if len(args) != 1 and len(args) != 0:
            raise CommandError("empty_asset_trashcan requires one or no arguments: |<location>|")

        locs = []

        if len(args) == 1:
            locs.append(CourseDescriptor.id_to_location(args[0]))
        else:
            courses = modulestore('direct').get_courses()
            for course in courses:
                locs.append(course.location)

        if query_yes_no("Emptying trashcan. Confirm?", default="no"):
            empty_asset_trashcan(locs)
