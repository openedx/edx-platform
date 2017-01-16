import os
import csv
from optparse import make_option

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError
from django.utils import translation

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.forms import AccountCreationForm
from student.models import CourseEnrollment, create_comments_service_user
from student.views import _do_create_account, AccountValidationError
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

    option_list = BaseCommand.option_list + (
        make_option('-m', '--mode',
                    metavar='ENROLLMENT_MODE',
                    dest='mode',
                    default='honor',
                    choices=('audit', 'verified', 'honor'),
                    help='Enrollment type for user for a specific course'),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=None,
                    help='course to enroll the user in (optional)')
    )

    def handle(self, *args, **options):
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        project_rel_filepath = 'employees.csv'
        path = '{}/{}'.format(BASE_DIR, project_rel_filepath)

        with open(path, 'r') as f:
            user_data_list = csv.DictReader(f)
            for row in user_data_list:
                name = row['name']
                email = row['email']
                password = row['pass']
                staff = int(row['is_staff'])
                username = email.split('@')[0].replace(".", "_")

                # parse out the course into a coursekey
                if options['course']:
                    try:
                        course = CourseKey.from_string(options['course'])
                    # if it's not a new-style course key, parse it from an old-style
                    # course key
                    except InvalidKeyError:
                        course = SlashSeparatedCourseKey.from_deprecated_string(options['course'])

                form = AccountCreationForm(
                    data={
                        'username': username,
                        'email': email,
                        'password': password,
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
                    user, _, reg = _do_create_account(form)
                    if staff == 1:
                        user.is_staff = True
                        user.save()
                    reg.activate()
                    reg.save()
                    create_comments_service_user(user)
                except AccountValidationError as e:
                    print e.message
                    user = User.objects.get(email=email)
                except ValidationError:
                    continue
                if options['course']:
                    CourseEnrollment.enroll(user, course, mode=options['mode'])
                translation.deactivate()
