"""
Management command to find all students that need certificates for
courses that have finished, and put their cert requests on the queue.
"""


import datetime
import logging

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from lms.djangoapps.certificates.api import generate_user_certificates
from lms.djangoapps.certificates.models import CertificateStatuses, certificate_status_for_student
from xmodule.modulestore.django import modulestore

LOGGER = logging.getLogger(__name__)
User = get_user_model()


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

    def add_arguments(self, parser):
        parser.add_argument(
            '-n', '--noop',
            action='store_true',
            dest='noop',
            help="Don't add certificate requests to the queue"
        )
        parser.add_argument(
            '--insecure',
            action='store_true',
            dest='insecure',
            help="Don't use https for the callback url to the LMS, useful in http test environments"
        )
        parser.add_argument(
            '-c', '--course',
            metavar='COURSE_ID',
            dest='course',
            required=True,
            help='Grade and generate certificates for a specific course'
        )
        parser.add_argument(
            '-f', '--force-gen',
            metavar='STATUS',
            dest='force',
            default=False,
            help='Will generate new certificates for only those users whose entry in the certificate table matches '
            'STATUS. STATUS can be generating, unavailable, deleted, error or notpassing.'
        )

    def handle(self, *args, **options):
        LOGGER.info(
            (
                "Starting to create tasks for ungenerated certificates "
                "with arguments %s and options %s"
            ),
            str(args),
            str(options)
        )

        # Will only generate a certificate if the current
        # status is in the unavailable state, can be set
        # to something else with the force flag

        if options['force']:
            valid_statuses = [getattr(CertificateStatuses, options['force'])]
        else:
            valid_statuses = [CertificateStatuses.unavailable]

        # Print update after this many students
        status_interval = 500

        course = CourseKey.from_string(options['course'])
        ended_courses = [course]

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
                if count % status_interval == 0:
                    # Print a status update with an approximation of
                    # how much time is left based on how long the last
                    # interval took
                    diff = datetime.datetime.now(UTC) - start
                    timeleft = diff * (total - count) / status_interval
                    hours, remainder = divmod(timeleft.seconds, 3600)
                    minutes, _seconds = divmod(remainder, 60)
                    print(f"{count}/{total} completed ~{hours:02}:{minutes:02}m remaining")
                    start = datetime.datetime.now(UTC)

                cert_status = certificate_status_for_student(student, course_key)['status']
                LOGGER.info(
                    (
                        "Student %s has certificate status '%s' "
                        "in course '%s'"
                    ),
                    student.id,
                    cert_status,
                    str(course_key)
                )

                if cert_status in valid_statuses:

                    if not options['noop']:
                        # Add the certificate request to the queue
                        generate_user_certificates(
                            student,
                            course_key,
                            course=course,
                            insecure=options['insecure']
                        )

                        LOGGER.info(f"Added a certificate generation task to the XQueue for student {student.id} in "
                                    f"course {course_key}.")

                    else:
                        LOGGER.info(
                            (
                                "Skipping certificate generation for "
                                "student %s in course '%s' "
                                "because the noop flag is set."
                            ),
                            student.id,
                            str(course_key)
                        )

                else:
                    LOGGER.info(
                        (
                            "Skipped student %s because "
                            "certificate status '%s' is not in %s"
                        ),
                        student.id,
                        cert_status,
                        str(valid_statuses)
                    )

            LOGGER.info(
                (
                    "Completed ungenerated certificates command "
                    "for course '%s'"
                ),
                str(course_key)
            )
