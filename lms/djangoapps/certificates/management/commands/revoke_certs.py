"""Django management command to change certificate status to unavailable"""

from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from certificates.models import GeneratedCertificate


class Command(BaseCommand):
    help = """Change the certificate status to unavailable"""

    option_list = BaseCommand.option_list + (
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="Don't grade or add certificate requests to the queue"),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='The course id (e.g., mit/6-002x/circuits-and-electronics) for which the student named in'
                         '<username> should be graded'),
        make_option('-u', '--user',
                    metavar='USERNAME',
                    dest='username',
                    default=False,
                    help='The username or email address for whom grading and certification should be requested'),
    )

    def handle(self, *args, **options):
        if options['course']:
            # try to parse out the course from the serialized form
            try:
                course_id = CourseKey.from_string(options['course'])
            except InvalidKeyError:
                print("Course id {} could not be parsed as a CourseKey; falling back to SSCK.from_dep_str".format(options['course']))
                course_id = SlashSeparatedCourseKey.from_deprecated_string(options['course'])
        else:
            raise CommandError("You must specify a course")

        user = options['username']
        if not (course_id and user):
            raise CommandError('both course id and student username are required')

        student = None
        if '@' in user:
            student = User.objects.get(email=user, courseenrollment__course_id=course_id)
        else:
            student = User.objects.get(username=user, courseenrollment__course_id=course_id)

        if not options['noop']:
            revoke = GeneratedCertificate.objects.get(user=student, course_id=course_id,)
            print "Revoking certificate for student {0} in {1}".format(student, course_id)
            revoke.status = 'unavailable'
            revoke.save()
        else:
            print "noop option given, would have revoked for student {0} in {1}".format(student, course_id)
