from django.core.management.base import BaseCommand, CommandError
from opaque_keys.edx.keys import CourseKey

from xmodule.contentstore.utils import empty_asset_trashcan
from xmodule.modulestore.django import modulestore

from .prompt import query_yes_no


class Command(BaseCommand):
    help = 'Empty the trashcan. Can pass an optional course_id to limit the damage.'

    def add_arguments(self, parser):
        parser.add_argument('course_id',
                            help='Course ID to empty, leave off to empty for all courses',
                            nargs='?')

    def handle(self, *args, **options):
        if options['course_id']:
            course_ids = [CourseKey.from_string(options['course_id'])]
        else:
            course_ids = [course.id for course in modulestore().get_courses()]

        if query_yes_no("Emptying {} trashcan(s). Confirm?".format(len(course_ids)), default="no"):
            empty_asset_trashcan(course_ids)
