import logging
from prettytable import PrettyTable

from django.core.management.base import BaseCommand, CommandError, make_option

from xmodule.modulestore.django import modulestore
from xmodule.modulestore import Location


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Usage: python manage.py cms --settings=aws check_draft --active_only edX/DemoX/Demo_Course

    Args:
        course_id: 'org/course/run'
    """
    help = """Usage: check_draft [--active_only] [<course_id>]"""

    option_list = BaseCommand.option_list + (
        make_option('--active_only',
                    default=False,
                    action='store_true',
                    help='Limit courses to active ones'),
    )

    def handle(self, *args, **options):
        if len(args) > 1:
            raise CommandError("check_draft requires one or no arguments: |<course_id>|")

        # Check args: course_id
        course_id = args[0] if len(args) > 0 else None
        if course_id:
            try:
                Location.parse_course_id(course_id)
            except ValueError:
                raise CommandError("The course_id is not of the right format. It should be like 'org/course/run'")

        # Check options: active_only
        active_only = options['active_only']

        # Result
        output = PrettyTable(['Course ID', 'Course Name', 'Chapter Name', 'Sequential Name', 'Vertical Name', 'Draft?'])
        output.align = 'l'

        # Find courses
        tag = 'i4x'
        if course_id:
            course_dict = Location.parse_course_id(course_id)
            org = course_dict['org']
            course = course_dict['course']
            name = course_dict['name']
            course_items = modulestore().get_items(Location(tag, org, course, 'course', name))
            if not course_items:
                raise CommandError("The specified course does not exist.")
        else:
            course_items = modulestore().get_courses()

        for course_item in course_items:
            # Note: Use only active courses
            if active_only and course_item.has_ended():
                continue
            # Find chapter items
            chapter_items = [modulestore().get_item(Location(item_id)) for item_id in course_item.children]
            chapter_items = sorted(chapter_items, key=lambda item: item.start)
            for chapter_item in chapter_items:
                # Find sequential items
                sequential_items = [modulestore().get_item(Location(item_id)) for item_id in chapter_item.children]
                sequential_items = sorted(sequential_items, key=lambda item: item.start)
                for sequential_item in sequential_items:
                    # Find vertical items
                    vertical_items = [modulestore().get_item(Location(item_id)) for item_id in sequential_item.children]
                    vertical_items = sorted(vertical_items, key=lambda item: item.start)
                    for vertical_item in vertical_items:
                        if vertical_item.is_draft:
                            output.add_row([course_item.id, course_item.display_name, chapter_item.display_name, sequential_item.display_name, vertical_item.display_name, vertical_item.is_draft])

        # Print result
        print output
