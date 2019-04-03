from __future__ import absolute_import, print_function

from django.conf import settings
from django.contrib.auth.models import User
from django.utils import translation
from opaque_keys.edx.keys import CourseKey
from six import text_type

from student.forms import AccountCreationForm
from student.helpers import AccountValidationError, do_create_account
from student.models import CourseEnrollment, create_comments_service_user
from track.management.tracked_command import TrackedCommand


class Command(TrackedCommand):
    help = """
    This command creates and registers a user in a given course
    as "audit", "verified" or "honor".

    example:
        # Enroll a user test@example.com into the demo course
        # The username and name will default to "test"
        manage.py ... create_user -e test@example.com -p insecure -c edX/Open_DemoX/edx_demo_course -m verified
    """

    def add_arguments(self, parser):
        parser.add_argument('-m', '--mode',
                            metavar='ENROLLMENT_MODE',
                            default='honor',
                            choices=('audit', 'verified', 'honor'),
                            help='Enrollment type for user for a specific course, defaults to "honor"')
        parser.add_argument('-u', '--username',
                            metavar='USERNAME',
                            help='Username, defaults to "user" in the email')
        parser.add_argument('-n', '--proper_name',
                            metavar='NAME',
                            help='Name, defaults to "user" in the email')
        parser.add_argument('-p', '--password',
                            metavar='PASSWORD',
                            help='Password for user',
                            required=True)
        parser.add_argument('-e', '--email',
                            metavar='EMAIL',
                            help='Email for user',
                            required=True)
        parser.add_argument('-c', '--course',
                            metavar='COURSE_ID',
                            help='Course to enroll the user in (optional)')
        parser.add_argument('-s', '--staff',
                            action='store_true',
                            help='Give user the staff bit, defaults to off')

    def handle(self, *args, **options):
        username = options['username'] if options['username'] else options['email'].split('@')[0]
        name = options['proper_name'] if options['proper_name'] else options['email'].split('@')[0]

        # parse out the course into a coursekey
        course = CourseKey.from_string(options['course']) if options['course'] else None

        form = AccountCreationForm(
            data={
                'username': username,
                'email': options['email'],
                'password': options['password'],
                'name': name,
            },
            tos_required=False
        )

        # django.utils.translation.get_language() will be used to set the new
        # user's preferred language.  This line ensures that the result will
        # match this installation's default locale.  Otherwise, inside a
        # management command, it will always return "en-us".
        translation.activate(settings.LANGUAGE_CODE)

        try:
            user, _, reg = do_create_account(form)
            if options['staff']:
                user.is_staff = True
                user.save()
            reg.activate()
            reg.save()
            create_comments_service_user(user)
        except AccountValidationError as e:
            print(text_type(e))
            user = User.objects.get(email=options['email'])

        if course:
            CourseEnrollment.enroll(user, course, mode=options['mode'])

        translation.deactivate()
