"""
    Command for deleting courses

    Arguments:
        arg1 (str): Course key of the course to delete

    Returns:
        none
"""
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey

from contentstore.utils import delete_course
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore

from .prompt import query_yes_no


class Command(BaseCommand):
    """
    Delete a MongoDB backed course
    Example usage:
        $ ./manage.py cms delete_course 'course-v1:edX+DemoX+Demo_Course' --settings=devstack
        $ ./manage.py cms delete_course 'course-v1:edX+DemoX+Demo_Course' --keep-instructors --settings=devstack

    Note:
        keep-instructors option is added in effort to delete duplicate courses safely.
        There happens to be courses with difference of casing in ids, for example
        course-v1:DartmouthX+DART.ENGL.01.X+2016_T1 is a duplicate of course-v1:DartmouthX+DART.ENGL.01.x+2016_T1
        (Note the differene in 'x' of course number). These two are independent courses in MongoDB.
        Current MYSQL setup is case-insensitive which essentially means there are not
        seperate entries (in all course related mysql tables, but here we are concerned about accesses)
        for duplicate courses.
        This option will make us able to delete course (duplicate one) from
        mongo while perserving course's related access data in mysql.
    """
    help = '''Delete a MongoDB backed course'''

    def add_arguments(self, parser):
        """
        Add arguments to the command parser.
        """
        parser.add_argument('course_key', help="ID of the course to delete.")

        parser.add_argument(
            '--keep-instructors',
            action='store_true',
            default=False,
            help='Do not remove permissions of users and groups for course',
        )

    def handle(self, *args, **options):
        try:
            course_key = CourseKey.from_string(options['course_key'])
        except InvalidKeyError:
            raise CommandError("Invalid course_key: '%s'." % options['course_key'])

        if not modulestore().get_course(course_key):
            raise CommandError("Course with '%s' key not found." % options['course_key'])

        print 'Going to delete the %s course from DB....' % options['course_key']
        if query_yes_no("Deleting course {0}. Confirm?".format(course_key), default="no"):
            if query_yes_no("Are you sure. This action cannot be undone!", default="no"):
                delete_course(course_key, ModuleStoreEnum.UserID.mgmt_command, options['keep_instructors'])
                print "Deleted course {}".format(course_key)
