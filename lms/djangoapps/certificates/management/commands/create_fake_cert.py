"""Utility for testing certificate display.

This command will create a fake certificate for a user
in a course.  The certificate will display on the student's
dashboard, but no PDF will be generated.

Example usage:

    $ ./manage.py lms create_fake_cert test_user edX/DemoX/Demo_Course --mode honor --grade 0.89

"""


import logging
from textwrap import dedent

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from opaque_keys.edx.keys import CourseKey
from six import text_type

from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate

LOGGER = logging.getLogger(__name__)


class Command(BaseCommand):
    """Create a fake certificate for a user in a course. """
    help = dedent(__doc__).strip()

    def add_arguments(self, parser):
        parser.add_argument(
            'username',
            metavar='USERNAME',
            help='Username of the user to create the fake cert for'
        )
        parser.add_argument(
            'course_key',
            metavar='COURSE_KEY',
            help='Course key of the course to grant the cert for'
        )

        parser.add_argument(
            '-m', '--mode',
            metavar='CERT_MODE',
            dest='cert_mode',
            default='honor',
            help='The course mode of the certificate (e.g. "honor", "verified", or "professional")'
        )

        parser.add_argument(
            '-s', '--status',
            metavar='CERT_STATUS',
            dest='status',
            default=CertificateStatuses.downloadable,
            help='The status of the certificate'
        )

        parser.add_argument(
            '-g', '--grade',
            metavar='CERT_GRADE',
            dest='grade',
            default='',
            help='The grade for the course, as a decimal (e.g. "0.89" for 89 percent)'
        )

    def handle(self, *args, **options):
        """Create a fake certificate for a user.

        Arguments:
            username (unicode): Identifier for the certificate's user.
            course_key (unicode): Identifier for the certificate's course.

        Keyword Arguments:
            cert_mode (str): The mode of the certificate (e.g "honor")
            status (str): The status of the certificate (e.g. "downloadable")
            grade (str): The grade of the certificate (e.g "0.89" for 89%)

        Raises:
            CommandError

        """
        user = User.objects.get(username=options['username'])
        course_key = CourseKey.from_string(options['course_key'])
        cert_mode = options.get('cert_mode', 'honor')
        status = options.get('status', CertificateStatuses.downloadable)
        grade = options.get('grade', '')

        cert, created = GeneratedCertificate.eligible_certificates.get_or_create(
            user=user,
            course_id=course_key
        )
        cert.mode = cert_mode
        cert.status = status
        cert.grade = grade

        if status == CertificateStatuses.downloadable:
            cert.download_uuid = 'test'
            cert.verify_uuid = 'test'
            cert.download_url = 'http://www.example.com'

        cert.save()

        if created:
            LOGGER.info(
                u"Created certificate for user %s in course %s "
                u"with mode %s, status %s, "
                u"and grade %s",
                user.id, text_type(course_key),
                cert_mode, status, grade
            )

        else:
            LOGGER.info(
                u"Updated certificate for user %s in course %s "
                u"with mode %s, status %s, "
                u"and grade %s",
                user.id, text_type(course_key),
                cert_mode, status, grade
            )
