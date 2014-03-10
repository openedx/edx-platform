from django.core.management.base import BaseCommand
from certificates.models import certificate_status_for_student
from certificates.queue import XQueueCertInterface
from django.contrib.auth.models import User
from optparse import make_option
from django.conf import settings
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from certificates.models import CertificateStatuses
import datetime
from pytz import UTC


class Command(BaseCommand):

    help = """
    Find all students that need certificates for courses that have finished and
    put their cert requests on the queue.

    If --user is given, only grade and certify the requested username.

    Use the --noop option to test without actually putting certificates on the
    queue to be generated.
    """

    option_list = BaseCommand.option_list + (
        make_option('-n', '--noop',
                    action='store_true',
                    dest='noop',
                    default=False,
                    help="Don't add certificate requests to the queue"),
        make_option('--insecure',
                    action='store_true',
                    dest='insecure',
                    default=False,
                    help="Don't use https for the callback url to the LMS, useful in http test environments"),
        make_option('-c', '--course',
                    metavar='COURSE_ID',
                    dest='course',
                    default=False,
                    help='Grade and generate certificates '
                    'for a specific course'),
        make_option('-f', '--force-gen',
                    metavar='STATUS',
                    dest='force',
                    default=False,
                    help='Will generate new certificates for only those users '
                    'whose entry in the certificate table matches STATUS. '
                    'STATUS can be generating, unavailable, deleted, error '
                    'or notpassing.'),
    )

    def handle(self, *args, **options):

        # Will only generate a certificate if the current
        # status is in the unavailable state, can be set
        # to something else with the force flag

        if options['force']:
            valid_statuses = getattr(CertificateStatuses, options['force'])
        else:
            valid_statuses = [CertificateStatuses.unavailable]

        # Print update after this many students

        STATUS_INTERVAL = 500

        if options['course']:
            ended_courses = [options['course']]
        else:
            # Find all courses that have ended
            ended_courses = []
            for course_id in [course  # all courses in COURSE_LISTINGS
                              for sub in settings.COURSE_LISTINGS
                              for course in settings.COURSE_LISTINGS[sub]]:
                course = modulestore().get_course(course_id)
                if course.has_ended():
                    ended_courses.append(course_id)

        for course_id in ended_courses:
            # prefetch all chapters/sequentials by saying depth=2
            course = modulestore().get_course(course_id, depth=2)

            print "Fetching enrolled students for {0}".format(course_id)
            enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_id).prefetch_related(
                    "groups").order_by('username')

            xq = XQueueCertInterface()
            if options['insecure']:
                xq.use_https = False
            total = enrolled_students.count()
            count = 0
            start = datetime.datetime.now(UTC)

            for student in enrolled_students:
                count += 1
                if count % STATUS_INTERVAL == 0:
                    # Print a status update with an approximation of
                    # how much time is left based on how long the last
                    # interval took
                    diff = datetime.datetime.now(UTC) - start
                    timeleft = diff * (total - count) / STATUS_INTERVAL
                    hours, remainder = divmod(timeleft.seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    print "{0}/{1} completed ~{2:02}:{3:02}m remaining".format(
                        count, total, hours, minutes)
                    start = datetime.datetime.now(UTC)

                if certificate_status_for_student(
                        student, course_id)['status'] in valid_statuses:
                    if not options['noop']:
                        # Add the certificate request to the queue
                        ret = xq.add_cert(student, course_id, course=course)
                        if ret == 'generating':
                            print '{0} - {1}'.format(student, ret)
