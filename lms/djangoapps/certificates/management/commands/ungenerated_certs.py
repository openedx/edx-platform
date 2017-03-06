"""
Management command to find all students that need certificates for
courses that have finished, and put their cert requests on the queue.
"""
import logging
import datetime
from pytz import UTC
from django.core.management.base import BaseCommand, CommandError
from certificates.models import certificate_status_for_student
from certificates.api import generate_user_certificates
from django.contrib.auth.models import User
from optparse import make_option
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.modulestore.django import modulestore
from certificates.models import CertificateStatuses


LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Management command to find all students that need certificates
    for courses that have finished and put their cert requests on the queue.
    """

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

        LOGGER.info(
            (
                u"Starting to create tasks for ungenerated certificates "
                u"with arguments %s and options %s"
            ),
            unicode(args),
            unicode(options)
        )

        # Will only generate a certificate if the current
        # status is in the unavailable state, can be set
        # to something else with the force flag

        if options['force']:
            valid_statuses = [getattr(CertificateStatuses, options['force'])]
        else:
            valid_statuses = [CertificateStatuses.unavailable]

        # Print update after this many students

        STATUS_INTERVAL = 500

        if options['course']:
            # try to parse out the course from the serialized form
            try:
                course = CourseKey.from_string(options['course'])
            except InvalidKeyError:
                LOGGER.warning(
                    (
                        u"Course id %s could not be parsed as a CourseKey; "
                        u"falling back to SlashSeparatedCourseKey.from_deprecated_string()"
                    ),
                    options['course']
                )
                course = SlashSeparatedCourseKey.from_deprecated_string(options['course'])
            ended_courses = [course]
        else:
            raise CommandError("You must specify a course")

        for course_key in ended_courses:
            # prefetch all chapters/sequentials by saying depth=2
            course = modulestore().get_course(course_key, depth=2)

            enrolled_students = User.objects.filter(
                courseenrollment__course_id=course_key
            )

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
                    minutes, _seconds = divmod(remainder, 60)
                    print "{0}/{1} completed ~{2:02}:{3:02}m remaining".format(
                        count, total, hours, minutes)
                    start = datetime.datetime.now(UTC)

                cert_status = certificate_status_for_student(student, course_key)['status']
                LOGGER.info(
                    (
                        u"Student %s has certificate status '%s' "
                        u"in course '%s'"
                    ),
                    student.id,
                    cert_status,
                    unicode(course_key)
                )

                if cert_status in valid_statuses:

                    if not options['noop']:
                        # Add the certificate request to the queue
                        ret = generate_user_certificates(
                            student,
                            course_key,
                            course=course,
                            insecure=options['insecure']
                        )

                        if ret == 'generating':
                            LOGGER.info(
                                (
                                    u"Added a certificate generation task to the XQueue "
                                    u"for student %s in course '%s'. "
                                    u"The new certificate status is '%s'."
                                ),
                                student.id,
                                unicode(course_key),
                                ret
                            )

                    else:
                        LOGGER.info(
                            (
                                u"Skipping certificate generation for "
                                u"student %s in course '%s' "
                                u"because the noop flag is set."
                            ),
                            student.id,
                            unicode(course_key)
                        )

                else:
                    LOGGER.info(
                        (
                            u"Skipped student %s because "
                            u"certificate status '%s' is not in %s"
                        ),
                        student.id,
                        cert_status,
                        unicode(valid_statuses)
                    )

            LOGGER.info(
                (
                    u"Completed ungenerated certificates command "
                    u"for course '%s'"
                ),
                unicode(course_key)
            )
