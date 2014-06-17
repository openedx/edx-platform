"""Django management command to force certificate regeneration for one user"""

from optparse import make_option
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from certificates.queue import XQueueCertInterface


class Command(BaseCommand):
    help = """Put a request on the queue to recreate the certificate for a particular user in a particular course."""

    option_list = BaseCommand.option_list + (
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="Don't grade or add certificate requests to the queue"),
        make_option('--insecure',
                    action='store_true',
                    dest='insecure',
                    default=False,
                    help="Don't use https for the callback url to the LMS, useful in http test environments"),
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
        make_option('-G', '--grade',
                    metavar='GRADE',
                    dest='grade_value',
                    default=None,
                    help='The grade string, such as "Distinction", which should be passed to the certificate agent'),
        make_option('-T', '--template',
                    metavar='TEMPLATE',
                    dest='template_file',
                    default=None,
                    help='The template file used to render this certificate, like "QMSE01-distinction.pdf"'),
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
        print "Fetching enrollment for student {0} in {1}".format(user, course_id)
        if '@' in user:
            student = User.objects.get(email=user, courseenrollment__course_id=course_id)
        else:
            student = User.objects.get(username=user, courseenrollment__course_id=course_id)

        print "Fetching course data for {0}".format(course_id)
        course = modulestore().get_course(course_id, depth=2)

        if not options['noop']:
            # Add the certificate request to the queue
            xq = XQueueCertInterface()
            if options['insecure']:
                xq.use_https = False
            ret = xq.regen_cert(student, course_id, course=course,
                                forced_grade=options['grade_value'],
                                template_file=options['template_file'])
            print '{0} - {1}'.format(student, ret)
        else:
            print "noop option given, skipping work queueing..."
