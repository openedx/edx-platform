"""
Management command to update the status of a single user certificate
for a given user, in a given course. If no --status kwarg is provided,
the status will be updated to CertificiateStatuses.unavailable.
"""
from __future__ import print_function

import logging
from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from certificates.models import CertificateStatuses
from certificates.models import GeneratedCertificate

LOGGER = logging.getLogger(__name__)

VALID_STATUSES = [
    CertificateStatuses.unavailable,
    CertificateStatuses.downloadable,
    CertificateStatuses.notpassing,
]


class Command(BaseCommand):
    """
    Update the status of a single user certificate for a given user in a given course
    """
    help = __doc__
    option_list = BaseCommand.option_list + (
        make_option(
            '-c', '--course-id',
            default=False,
            help='The course id (e.g. mit/6-002x/circuits-and-electronics or course-v1:edX+DemoX+Demo_Course)'
                 ' of the course in which the certificate of the student should be updated',
        ),
        make_option(
            '-u', '--username-or-email',
            default=False,
            help='The username or email address for whom grading and certificate status should be updated',
        ),
        make_option(
            '-s', '--status',
            default=CertificateStatuses.unavailable,
            help='The status to set to the corresponding certificate',
        ),
    )

    def handle(self, *args, **options):
        if options['course_id']:
            # try to parse out the course from the serialized form
            try:
                course_id = CourseKey.from_string(options['course_id'])
            except InvalidKeyError:
                course_id = SlashSeparatedCourseKey.from_deprecated_string(options['course_id'])
        else:
            raise CommandError(u'course-id is required')

        user = options['username_or_email']
        if not user:
            raise CommandError(u'username-or-email is required')

        status = options['status']

        if status not in VALID_STATUSES:
            raise CommandError(
                u"INVALID STATUS. "
                "Supported Statuses: {statuses}".format(
                    statuses=', '.join(
                        "`{status}`".format(
                            status=status
                        )
                        for status in VALID_STATUSES
                    )
                )
            )

        if '@' in user:
            student = User.objects.get(email=user, courseenrollment__course_id=course_id)
        else:
            student = User.objects.get(username=user, courseenrollment__course_id=course_id)
        try:
            certificate = GeneratedCertificate.objects.get(user=student, course_id=course_id)
            certificate.status = status
            certificate.save()
            cert_saved_msg = (
                u"""The certificate status for student {student_id}
                in course '{course_id}'
                has been set to '{status}'""".format(
                    student_id=student.id,
                    course_id=course_id,
                    status=certificate.status,
                )
            )
            LOGGER.info(cert_saved_msg)
            # Print cert_saved_msg to sys.stdout, so that it is viewable in sysadmin
            print(cert_saved_msg)
        except GeneratedCertificate.DoesNotExist:
            LOGGER.error(
                (
                    u"Certificate for student %d in course %s does not exist"
                ),
                student.id,
                course_id,
            )
            raise
