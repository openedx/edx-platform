import logging
from prettytable import PrettyTable

from django.core.management.base import BaseCommand, CommandError, make_option

from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import CourseLocator


log = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Usage: python manage.py cms --settings=aws check_draft --active_only edX/DemoX/Demo_Course

    Args:
        course_id: 'org/course/run' or 'course-v1:org+course+run'
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
                course_id = CourseLocator.from_string(course_id)
            except InvalidKeyError:
                raise CommandError("The course_id is not of the right format. It should be like 'org/course/run' or 'course-v1:org+course+run'")

        # Check options: active_only
        active_only = options['active_only']

        # Result
        output = PrettyTable(['Course ID', 'Course Name', 'Chapter Name', 'Sequential Name', 'Vertical Name', 'Draft?', 'Changed?'])
        output.align = 'l'

        # Find courses
        if course_id:
            course_items = modulestore().get_items(course_id, qualifiers={'category': 'course'})
            if not course_items:
                raise CommandError("The specified course does not exist.")
        else:
            course_items = modulestore().get_courses()

        for course_item in course_items:
            # Note: Use only active courses
            if active_only and course_item.has_ended():
                continue
            # Find chapter items
            chapter_items = [modulestore().get_item(item.location) for item in course_item.get_children()]
            chapter_items = sorted(chapter_items, key=lambda item: item.start)
            for chapter_item in chapter_items:
                # Find sequential items
                sequential_items = [modulestore().get_item(item.location) for item in chapter_item.get_children()]
                sequential_items = sorted(sequential_items, key=lambda item: item.start)
                for sequential_item in sequential_items:
                    #print "sequential_item.location=%s" % sequential_item.location
                    #print "sequential_item.published?=%s" % modulestore().has_item(sequential_item.location, revision=ModuleStoreEnum.RevisionOption.published_only)
                    #print "sequential_item.changed?=%s" % modulestore().has_changes(sequential_item)
                    # Find vertical items
                    vertical_items = [modulestore().get_item(item.location) for item in sequential_item.get_children()]
                    vertical_items = sorted(vertical_items, key=lambda item: item.start)
                    for vertical_item in vertical_items:
                        #print "vertical_item.location=%s" % vertical_item.location
                        #print "vertical_item.published?=%s" % modulestore().has_item(vertical_item.location, revision=ModuleStoreEnum.RevisionOption.published_only)
                        #print "vertical_item.changed?=%s" % modulestore().has_changes(vertical_item)
                        is_draft = vertical_item.is_draft
                        # Note: cribbed from cms/djangoapps/contentstore/views/tests/test_item.py
                        has_changes = modulestore().has_changes(vertical_item)
                        if is_draft or has_changes:
                            output.add_row([course_item.id, course_item.display_name, chapter_item.display_name, sequential_item.display_name, vertical_item.display_name, is_draft, has_changes])

        # Print result
        print output
