""" Management command to create test users """
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.management.commands._create_users import create_users


def user_info_generator(usernames, password, domain):
    for username in usernames:
        yield {
            'username': username,
            'email': f'{username}@{domain}',
            'password': password,
            'name': username,
        }


class Command(BaseCommand):
    """
    Create test users with the given usernames and modes and enrolls them in the given course.

    Usage: create_test_users.py username1 ... usernameN [--course] [--mode] [--password] [--domain] [--course_staff]

    Examples:
    create_test_users.py
    create_test_users.py user1 --course MITx/6.002x/2012_Fall --domain testuniversity.edu
    create_test_users.py testmasters1 testmasters2 --course HarvardX/CS50x/2012 --mode masters
    create_test_users.py testcoursestaff1 testcoursestaff2 --course DemoX/MS12/1 --course_staff --password testpassword
    """

    def add_arguments(self, parser):
        parser.add_argument(
            'usernames',
            help='Usernames to use for created users.',
            nargs='+'
        )
        parser.add_argument(
            '--course',
            help='Add newly created users to this course',
            type=CourseKey.from_string
        )
        parser.add_argument(
            '--mode',
            help='The enrollment mode for the test users. If --course is not provided, this is ignored',
            default='audit',
            choices=CourseMode.ALL_MODES
        )
        parser.add_argument(
            '--password',
            help='Password to use for all created users.',
            default='12345'
        )
        parser.add_argument(
            '--domain',
            help='Domain for email addresses for created accounts',
            default='example.com'
        )
        parser.add_argument(
            '--course_staff',
            help=(
                'If present, users are created as course staff. --mode, if specified, is ignored. '
                'If --course is not provided, this is ignored'
            ),
            action='store_true'
        )
        parser.add_argument(
            '--ignore_user_already_exists',
            help="Don't fail if a user already exists. Log the error and attempt to enroll them in the course.",
            action='store_true'
        )

    def handle(self, *args, **options):
        course_key = options['course']
        course_staff = options['course_staff'] if course_key else None
        enrollment_mode = options['mode'] if course_key and not course_staff else None
        create_users(
            course_key,
            user_info_generator(
                options['usernames'],
                options['password'],
                options['domain']
            ),
            enrollment_mode=enrollment_mode,
            course_staff=course_staff,
            activate=True,
            ignore_user_already_exists=options['ignore_user_already_exists']
        )
