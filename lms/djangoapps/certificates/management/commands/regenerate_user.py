"""Django management command to force certificate regeneration for one user"""

from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from certificates.queue import XQueueCertInterface
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore


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
    )

    def handle(self, *args, **options):

        user = options['username']
        course_id = options['course']
        if not (course_id and user):
            raise CommandError('both course id and student username are required')

        student = None
        print "Fetching enrollment for student {0} in {1}".format(user, course_id)
        if '@' in user:
            student = User.objects.get(email=user, courseenrollment__course_id=course_id)
        else:
            student = User.objects.get(username=user, courseenrollment__course_id=course_id)

        print "Fetching course data for {0}".format(course_id)
        course = modulestore().get_instance(course_id, CourseDescriptor.id_to_location(course_id), depth=2)

        if not options['noop']:
            # Add the certificate request to the queue
            xq = XQueueCertInterface()
            if options['insecure']:
                xq.use_https = False
            ret = xq.regen_cert(student, course_id, course=course)
            print '{0} - {1}'.format(student, ret)
        else:
            print "noop option given, skipping work queueing..."
