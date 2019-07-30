from __future__ import print_function

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import translation

from opaque_keys.edx.keys import CourseKey
from six import text_type

from student.forms import AccountCreationForm
from student.helpers import do_create_account
from student.models import CourseEnrollment, create_comments_service_user
from student.helpers import AccountValidationError
from track.management.tracked_command import TrackedCommand

import csv


class Command(TrackedCommand):
    help = """
    This command creates and registers a list of users in a
    given course as "audit", "verified" or "honor".

    A csv with the format "name,email,expected_username,password"
    must be provided.

    example:
        # Enroll a user test@example.com into the demo course
        # The username and name will default to "test"
        manage.py ... create_user_bulk -f users.csv -c edX/Open_DemoX/edx_demo_course -m honor
    """

    def add_arguments(self, parser):
        parser.add_argument('-m', '--mode',
                            metavar='ENROLLMENT_MODE',
                            default='honor',
                            choices=('audit', 'verified', 'honor'),
                            help='Enrollment type for user for a specific course, defaults to "honor"')
        parser.add_argument('-c', '--course',
                            metavar='COURSE_ID',
                            help='Course to enroll the user in (optional)')
        parser.add_argument('-f', '--file',
                            metavar='filename',
                            help='CSV file containing the "name,email,expected_username,password" triplet, without a header')

    def generate_username(self, expected_username):
        """Try multiple algorithms to generate an username."""

        # Check the expected username
        if not User.objects.filter(username=expected_username).exists():
            return expected_username

        # Default case, use a numeric id to deduplicate
        id = 1
        while User.objects.filter(username=(expected_username + str(id))).exists():
            id += 1
        return (expected_username + str(id))

    def handle(self, *args, **options):
        # parse out the course into a coursekey
        course = CourseKey.from_string(options['course']) if options['course'] else None
        mode = options['mode']

        # django.utils.translation.get_language() will be used to set the new
        # user's preferred language.  This line ensures that the result will
        # match this installation's default locale.  Otherwise, inside a
        # management command, it will always return "en-us".
        translation.activate(settings.LANGUAGE_CODE)

        with open(options['file']) as file:
            fieldnames = ['name', 'email', 'expected_username', 'password']
            csv_reader = csv.DictReader(file, delimiter=',', fieldnames=fieldnames)
            for row in csv_reader:
                name = row['name']
                email = row['email']
                password = row['password']
                username = self.generate_username(row['expected_username'])

                if not User.objects.filter(email=email).exists():
                    form = AccountCreationForm(
                        data={
                            'username': username,
                            'email': email,
                            'password': password,
                            'name': name,
                        },
                        tos_required=False
                    )

                    try:
                        user, _, reg = do_create_account(form)
                        reg.activate()
                        reg.save()
                        create_comments_service_user(user)
                    except AccountValidationError as e:
                        print(text_type(e))
                else:
                    print('Email {} already registered{}'.format(email, ', only registering course.' if course else '.'))

                if course:
                    user = User.objects.get(email=email)
                    CourseEnrollment.enroll(user, course, mode=mode)

        translation.deactivate()
