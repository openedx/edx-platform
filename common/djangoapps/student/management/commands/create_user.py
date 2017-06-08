from optparse import make_option

from django.conf import settings
from django.contrib.auth.hashers import is_password_usable
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
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
        make_option('-u', '--username',
                    metavar='USERNAME',
                    dest='username',
                    default=None,
                    help='Username, defaults to "user" in the email'),
        make_option('-n', '--name',
                    metavar='NAME',
                    dest='name',
                    default=None,
                    help='Name, defaults to "user" in the email'),
        make_option('-p', '--password',
                    metavar='PASSWORD',
                    dest='password',
                    default=None,
                    help='Password for user'),
        make_option('--password-hash',
                    dest='password_hash',
                    default=False,
                    action='store_true',
                    help='Indicate that the provided password is a password hash'),
        make_option('--disabled-password',
                    dest='disabled_password',
                    default=False,
                    action='store_true',
                    help='Create account without valid password, so the user needs to use the '
                    'password recovery to be able to log in'),
        make_option('-e', '--email',
                    metavar='EMAIL',
                    dest='email',
                    default=None,
                    help='Email for user'),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=None,
                    help='course to enroll the user in (optional)'),
        make_option('-s', '--staff',
                    dest='staff',
                    default=False,
                    action='store_true',
                    help='give user the staff bit'),
    )

    def handle(self, *args, **options):
        username = options['username']
        name = options['name']
        if options['disabled_password']:
            # If a disabled password is requested, we first generate a random password,
            # since AccountCreationForm requires one.
            password = User.objects.make_random_password(length=32)
        else:
            password = options['password']
        if not username:
            username = options['email'].split('@')[0]
        if not name:
            name = options['email'].split('@')[0]

        # parse out the course into a coursekey
        if options['course']:
            try:
                course = CourseKey.from_string(options['course'])
            # if it's not a new-style course key, parse it from an old-style
            # course key
            except InvalidKeyError:
                course = SlashSeparatedCourseKey.from_deprecated_string(options['course'])

        if options['password_hash'] and not is_password_usable(password):
            raise CommandError('The provided password hash is invalid.')

        form = AccountCreationForm(
            data={
                'username': username,
                'email': options['email'],
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
            if options['staff']:
                user.is_staff = True
            if options['password_hash']:
                user.password = password
            if options['disabled_password']:
                user.set_password(None)
            user.save()
            reg.activate()
            reg.save()
            create_comments_service_user(user)
        except (AccountValidationError, ValidationError) as exception:
            self.stderr.write(exception.message)
            user = User.objects.get(email=options['email'])
        if options['course']:
            CourseEnrollment.enroll(user, course, mode=options['mode'])
        translation.deactivate()
