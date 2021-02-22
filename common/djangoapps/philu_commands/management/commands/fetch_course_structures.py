"""
Django management command to fetch course structures for given course ids
"""
import json
from logging import getLogger

from django.core.management.base import BaseCommand

from opaque_keys.edx.keys import CourseKey
from opaque_keys import InvalidKeyError
from philu_commands.helpers import generate_course_structure

log = getLogger(__name__)


class Command(BaseCommand):
    help = """
    This command prints the course structure for all the course ids given in arguments
    example:
        manage.py ... fetch_course_structures course_id_1 course_id_2
    """

    def add_arguments(self, parser):
        parser.add_argument('course_ids', nargs='+', help='Course ids for which we require the course structures.')

    def handle(self, *args, **options):
        course_structures = []
        course_ids = options['course_ids']

        for course_id in course_ids:
            try:
                course_key = CourseKey.from_string(course_id)
            except InvalidKeyError:
                log.error('Invalid course id provided: {}'.format(course_id))
                continue

            course_structure = generate_course_structure(course_key)
            course_structure['course_id'] = course_id
            course_structures.append(course_structure)

        if course_structures:
            print('-' * 80)
            print('Course structures for given course ids: ')
            print(json.dumps(course_structures))
            print('-' * 80)
        else:
            log.error('All course ids provided are invalid')
