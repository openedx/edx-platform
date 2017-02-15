"""Tests for the resubmit_error_certificates management command. """
import ddt
from django.core.management.base import CommandError
from nose.plugins.attrib import attr
from django.test.utils import override_settings
from mock import patch

from course_modes.models import CourseMode
from opaque_keys.edx.locator import CourseLocator

from badges.events.course_complete import get_completion_badge
from badges.models import BadgeAssertion
from badges.tests.factories import BadgeAssertionFactory, CourseCompleteImageConfigurationFactory
from lms.djangoapps.grades.tests.utils import mock_passing_grade
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, check_mongo_calls, ItemFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from certificates.management.commands import resubmit_error_certificates, regenerate_user, ungenerated_certs
from certificates.models import GeneratedCertificate, CertificateStatuses


class CertificateManagementTest(ModuleStoreTestCase):
    """
    Base test class for Certificate Management command tests.
    """
    # Override with the command module you wish to test.
    command = resubmit_error_certificates

    def setUp(self):
        super(CertificateManagementTest, self).setUp()
        self.user = UserFactory.create()
        self.courses = [
            CourseFactory.create()
            for __ in range(3)
        ]
        for course in self.courses:
            chapter = ItemFactory.create(parent_location=course.location)
            ItemFactory.create(parent_location=chapter.location, category='sequential', graded=True)
        CourseCompleteImageConfigurationFactory.create()

    def _create_cert(self, course_key, user, status, mode=CourseMode.HONOR):
        """Create a certificate entry. """
        # Enroll the user in the course
        CourseEnrollmentFactory.create(
            user=user,
            course_id=course_key,
            mode=mode
        )

        # Create the certificate
        GeneratedCertificate.eligible_certificates.create(
            user=user,
            course_id=course_key,
            status=status
        )

    def _run_command(self, *args, **kwargs):
        """Run the management command to generate a fake cert. """
        command = self.command.Command()
        return command.handle(*args, **kwargs)

    def _assert_cert_status(self, course_key, user, expected_status):
        """Check the status of a certificate. """
        cert = GeneratedCertificate.eligible_certificates.get(user=user, course_id=course_key)
        self.assertEqual(cert.status, expected_status)


@attr(shard=1)
@ddt.ddt
class ResubmitErrorCertificatesTest(CertificateManagementTest):
    """Tests for the resubmit_error_certificates management command. """

    @ddt.data(CourseMode.HONOR, CourseMode.VERIFIED)
    def test_resubmit_error_certificate(self, mode):
        # Create a certificate with status 'error'
        self._create_cert(self.courses[0].id, self.user, CertificateStatuses.error, mode)

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


@ddt.ddt
@attr(shard=1)
class RegenerateCertificatesTest(CertificateManagementTest):
    """
    Tests for regenerating certificates.
    """
    command = regenerate_user

    def setUp(self):
        """
        We just need one course here.
        """
        super(RegenerateCertificatesTest, self).setUp()
        self.course = self.courses[0]

    @ddt.data(True, False)
    @override_settings(CERT_QUEUE='test-queue')
    @patch('certificates.api.XQueueCertInterface', spec=True)
    def test_clear_badge(self, issue_badges, xqueue):
        """
        Given that I have a user with a badge
        If I run regeneration for a user
        Then certificate generation will be requested
        And the badge will be deleted if badge issuing is enabled
        """
        key = self.course.location.course_key
        self._create_cert(key, self.user, CertificateStatuses.downloadable)
        badge_class = get_completion_badge(key, self.user)
        BadgeAssertionFactory(badge_class=badge_class, user=self.user)
        self.assertTrue(BadgeAssertion.objects.filter(user=self.user, badge_class=badge_class))
        self.course.issue_badges = issue_badges
        self.store.update_item(self.course, None)
        self._run_command(
            username=self.user.email, course=unicode(key), noop=False, insecure=False, template_file=None,
            grade_value=None
        )
        xqueue.return_value.regen_cert.assert_called_with(
            self.user,
            key,
            course=self.course,
            forced_grade=None,
            template_file=None,
            generate_pdf=True
        )
        self.assertEquals(
            bool(BadgeAssertion.objects.filter(user=self.user, badge_class=badge_class)), not issue_badges
        )

    @override_settings(CERT_QUEUE='test-queue')
    @patch('capa.xqueue_interface.XQueueInterface.send_to_queue', spec=True)
    def test_regenerating_certificate(self, mock_send_to_queue):
        """
        Given that I have a user who has not passed course
        If I run regeneration for that user
        Then certificate generation will be not be requested
        """
        key = self.course.location.course_key
        self._create_cert(key, self.user, CertificateStatuses.downloadable)
        self._run_command(
            username=self.user.email, course=unicode(key), noop=False, insecure=True, template_file=None,
            grade_value=None
        )
        certificate = GeneratedCertificate.eligible_certificates.get(
            user=self.user,
            course_id=key
        )
        self.assertEqual(certificate.status, CertificateStatuses.notpassing)
        self.assertFalse(mock_send_to_queue.called)


@attr(shard=1)
class UngenerateCertificatesTest(CertificateManagementTest):
    """
    Tests for generating certificates.
    """
    command = ungenerated_certs

    def setUp(self):
        """
        We just need one course here.
        """
        super(UngenerateCertificatesTest, self).setUp()
        self.course = self.courses[0]

    @override_settings(CERT_QUEUE='test-queue')
    @patch('capa.xqueue_interface.XQueueInterface.send_to_queue', spec=True)
    def test_ungenerated_certificate(self, mock_send_to_queue):
        """
        Given that I have ended course
        If I run ungenerated certs command
        Then certificates should be generated for all users who passed course
        """
        mock_send_to_queue.return_value = (0, "Successfully queued")
        key = self.course.location.course_key
        self._create_cert(key, self.user, CertificateStatuses.unavailable)
        with mock_passing_grade():
            self._run_command(
                course=unicode(key), noop=False, insecure=True, force=False
            )
        self.assertTrue(mock_send_to_queue.called)
        certificate = GeneratedCertificate.eligible_certificates.get(
            user=self.user,
            course_id=key
        )
        self.assertEqual(certificate.status, CertificateStatuses.generating)
