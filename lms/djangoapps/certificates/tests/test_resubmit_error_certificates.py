"""Tests for the resubmit_error_certificates management command. """
import ddt
from django.core.management.base import CommandError

from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from certificates.management.commands import resubmit_error_certificates
from certificates.models import GeneratedCertificate, CertificateStatuses


@ddt.ddt
class ResubmitErrorCertificatesTest(ModuleStoreTestCase):
    """Tests for the resubmit_error_certificates management command. """

    def setUp(self):
        super(ResubmitErrorCertificatesTest, self).setUp()
        self.user = UserFactory.create()
        self.courses = [
            CourseFactory.create()
            for __ in range(3)
        ]

    def test_resubmit_error_certificate(self):
        # Create a certificate with status 'error'
        self._create_cert(self.courses[0].id, self.user, CertificateStatuses.error)

        # Re-submit all certificates with status 'error'
        with check_mongo_calls(1):
            self._run_command()

        # Expect that the certificate was re-submitted
        self._assert_cert_status(self.courses[0].id, self.user, CertificateStatuses.notpassing)

    def test_resubmit_error_certificate_in_a_course(self):
        # Create a certificate with status 'error'
        # in three courses.
        for idx in range(3):
            self._create_cert(self.courses[idx].id, self.user, CertificateStatuses.error)

        # Re-submit certificates for two of the courses
        self._run_command(course_key_list=[
            unicode(self.courses[0].id),
            unicode(self.courses[1].id)
        ])

        # Expect that the first two courses have been re-submitted,
        # but not the third course.
        self._assert_cert_status(self.courses[0].id, self.user, CertificateStatuses.notpassing)
        self._assert_cert_status(self.courses[1].id, self.user, CertificateStatuses.notpassing)
        self._assert_cert_status(self.courses[2].id, self.user, CertificateStatuses.error)

    @ddt.data(
        CertificateStatuses.deleted,
        CertificateStatuses.deleting,
        CertificateStatuses.downloadable,
        CertificateStatuses.generating,
        CertificateStatuses.notpassing,
        CertificateStatuses.regenerating,
        CertificateStatuses.restricted,
        CertificateStatuses.unavailable,
    )
    def test_resubmit_error_certificate_skips_non_error_certificates(self, other_status):
        # Create certificates with an error status and some other status
        self._create_cert(self.courses[0].id, self.user, CertificateStatuses.error)
        self._create_cert(self.courses[1].id, self.user, other_status)

        # Re-submit certificates for all courses
        self._run_command()

        # Only the certificate with status "error" should have been re-submitted
        self._assert_cert_status(self.courses[0].id, self.user, CertificateStatuses.notpassing)
        self._assert_cert_status(self.courses[1].id, self.user, other_status)

    def test_resubmit_error_certificate_none_found(self):
        self._create_cert(self.courses[0].id, self.user, CertificateStatuses.downloadable)
        self._run_command()
        self._assert_cert_status(self.courses[0].id, self.user, CertificateStatuses.downloadable)

    def test_course_caching(self):
        # Create multiple certificates for the same course
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)
        self._create_cert(self.courses[0].id, UserFactory.create(), CertificateStatuses.error)

        # Verify that we make only one Mongo query
        # because the course is cached.
        with check_mongo_calls(1):
            self._run_command()

    def test_invalid_course_key(self):
        invalid_key = u"invalid/"
        with self.assertRaisesRegexp(CommandError, invalid_key):
            self._run_command(course_key_list=[invalid_key])

    def test_course_does_not_exist(self):
        phantom_course = CourseLocator(org='phantom', course='phantom', run='phantom')
        self._create_cert(phantom_course, self.user, 'error')
        self._run_command()

        # Expect that the certificate was NOT resubmitted
        # since the course doesn't actually exist.
        self._assert_cert_status(phantom_course, self.user, CertificateStatuses.error)

    def _create_cert(self, course_key, user, status):
        """Create a certificate entry. """
        # Enroll the user in the course
        CourseEnrollmentFactory.create(
            user=user,
            course_id=course_key
        )

        # Create the certificate
        GeneratedCertificate.objects.create(
            user=user,
            course_id=course_key,
            status=status
        )

    def _run_command(self, *args, **kwargs):
        """Run the management command to generate a fake cert. """
        command = resubmit_error_certificates.Command()
        return command.handle(*args, **kwargs)

    def _assert_cert_status(self, course_key, user, expected_status):
        """Check the status of a certificate. """
        cert = GeneratedCertificate.objects.get(user=user, course_id=course_key)
        self.assertEqual(cert.status, expected_status)
