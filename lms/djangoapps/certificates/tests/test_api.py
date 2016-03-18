"""Tests for the certificates Python API. """
from contextlib import contextmanager
import ddt

from django.test import TestCase, RequestFactory
from django.test.utils import override_settings
from django.conf import settings
from mock import patch
from nose.plugins.attrib import attr

from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from course_modes.models import CourseMode
from course_modes.tests.factories import CourseModeFactory
from config_models.models import cache
from util.testing import EventTestMixin

from certificates import api as certs_api
from certificates.models import (
    CertificateStatuses,
    CertificateGenerationConfiguration,
    ExampleCertificate,
    GeneratedCertificate,
    certificate_status_for_student,
)
from certificates.queue import XQueueCertInterface, XQueueAddToQueueError
from certificates.tests.factories import GeneratedCertificateFactory

FEATURES_WITH_CERTS_ENABLED = settings.FEATURES.copy()
FEATURES_WITH_CERTS_ENABLED['CERTIFICATES_HTML_VIEW'] = True


class WebCertificateTestMixin(object):
    """
    Mixin with helpers for testing Web Certificates.
    """
    @contextmanager
    def _mock_passing_grade(self):
        """
        Mock the grading function to always return a passing grade.
        """
        symbol = 'courseware.grades.grade'
        with patch(symbol) as mock_grade:
            mock_grade.return_value = {'grade': 'Pass', 'percent': 0.75}
            yield

    @contextmanager
    def _mock_queue(self, is_successful=True):
        """
        Mock the "send to XQueue" method to return either success or an error.
        """
        symbol = 'capa.xqueue_interface.XQueueInterface.send_to_queue'
        with patch(symbol) as mock_send_to_queue:
            if is_successful:
                mock_send_to_queue.return_value = (0, "Successfully queued")
            else:
                mock_send_to_queue.side_effect = XQueueAddToQueueError(1, self.ERROR_REASON)

            yield mock_send_to_queue

    def _setup_course_certificate(self):
        """
        Creates certificate configuration for course
        """
        certificates = [
            {
                'id': 1,
                'name': 'Test Certificate Name',
                'description': 'Test Certificate Description',
                'course_title': 'tes_course_title',
                'signatories': [],
                'version': 1,
                'is_active': True
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.course.cert_html_view_enabled = True
        self.course.save()
        self.store.update_item(self.course, self.user.id)


@attr('shard_1')
class CertificateDownloadableStatusTests(WebCertificateTestMixin, ModuleStoreTestCase):
    """Tests for the `certificate_downloadable_status` helper function. """

    def setUp(self):
        super(CertificateDownloadableStatusTests, self).setUp()

        self.student = UserFactory()
        self.student_no_cert = UserFactory()
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course'
        )

        self.request_factory = RequestFactory()

    def test_cert_status_with_generating(self):
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )
        self.assertEqual(
            certs_api.certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': True,
                'download_url': None,
                'uuid': None,
            }
        )

    def test_cert_status_with_error(self):
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.error,
            mode='verified'
        )

        self.assertEqual(
            certs_api.certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': True,
                'download_url': None,
                'uuid': None
            }
        )

    def test_without_cert(self):
        self.assertEqual(
            certs_api.certificate_downloadable_status(self.student_no_cert, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': False,
                'download_url': None,
                'uuid': None,
            }
        )

    def verify_downloadable_pdf_cert(self):
        """
        Verifies certificate_downloadable_status returns the
        correct response for PDF certificates.
        """
        cert = GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com',
        )

        self.assertEqual(
            certs_api.certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': True,
                'is_generating': False,
                'download_url': 'www.google.com',
                'uuid': cert.verify_uuid
            }
        )

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True})
    def test_pdf_cert_with_html_enabled(self):
        self.verify_downloadable_pdf_cert()

    def test_pdf_cert_with_html_disabled(self):
        self.verify_downloadable_pdf_cert()

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True})
    def test_with_downloadable_web_cert(self):
        CourseEnrollment.enroll(self.student, self.course.id, mode='honor')
        self._setup_course_certificate()
        with self._mock_passing_grade():
            certs_api.generate_user_certificates(self.student, self.course.id)

        cert_status = certificate_status_for_student(self.student, self.course.id)
        self.assertEqual(
            certs_api.certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': True,
                'is_generating': False,
                'download_url': '/certificates/user/{user_id}/course/{course_id}'.format(
                    user_id=self.student.id,  # pylint: disable=no-member
                    course_id=self.course.id,
                ),
                'uuid': cert_status['uuid']
            }
        )


@attr('shard_1')
@override_settings(CERT_QUEUE='certificates')
class GenerateUserCertificatesTest(EventTestMixin, WebCertificateTestMixin, ModuleStoreTestCase):
    """Tests for generating certificates for students. """

    ERROR_REASON = "Kaboom!"

    def setUp(self):  # pylint: disable=arguments-differ
        super(GenerateUserCertificatesTest, self).setUp('certificates.api.tracker')

        self.student = UserFactory.create(
            email='joe_user@edx.org',
            username='joeuser',
            password='foo'
        )
        self.student_no_cert = UserFactory()
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course',
            grade_cutoffs={'cutoff': 0.75, 'Pass': 0.5}
        )
        self.enrollment = CourseEnrollment.enroll(self.student, self.course.id, mode='honor')
        self.request_factory = RequestFactory()

    def test_new_cert_requests_into_xqueue_returns_generating(self):
        with self._mock_passing_grade():
            with self._mock_queue():
                certs_api.generate_user_certificates(self.student, self.course.id)

        # Verify that the certificate has status 'generating'
        cert = GeneratedCertificate.eligible_certificates.get(user=self.student, course_id=self.course.id)
        self.assertEqual(cert.status, CertificateStatuses.generating)
        self.assert_event_emitted(
            'edx.certificate.created',
            user_id=self.student.id,
            course_id=unicode(self.course.id),
            certificate_url=certs_api.get_certificate_url(self.student.id, self.course.id),
            certificate_id=cert.verify_uuid,
            enrollment_mode=cert.mode,
            generation_mode='batch'
        )

    def test_xqueue_submit_task_error(self):
        with self._mock_passing_grade():
            with self._mock_queue(is_successful=False):
                certs_api.generate_user_certificates(self.student, self.course.id)

        # Verify that the certificate has been marked with status error
        cert = GeneratedCertificate.eligible_certificates.get(user=self.student, course_id=self.course.id)
        self.assertEqual(cert.status, 'error')
        self.assertIn(self.ERROR_REASON, cert.error_reason)

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': True})
    def test_new_cert_requests_returns_generating_for_html_certificate(self):
        """
        Test no message sent to Xqueue if HTML certificate view is enabled
        """
        self._setup_course_certificate()
        with self._mock_passing_grade():
            certs_api.generate_user_certificates(self.student, self.course.id)

        # Verify that the certificate has status 'downloadable'
        cert = GeneratedCertificate.eligible_certificates.get(user=self.student, course_id=self.course.id)
        self.assertEqual(cert.status, CertificateStatuses.downloadable)

    @patch.dict(settings.FEATURES, {'CERTIFICATES_HTML_VIEW': False})
    def test_cert_url_empty_with_invalid_certificate(self):
        """
        Test certificate url is empty if html view is not enabled and certificate is not yet generated
        """
        url = certs_api.get_certificate_url(self.student.id, self.course.id)
        self.assertEqual(url, "")


@attr('shard_1')
@ddt.ddt
class CertificateGenerationEnabledTest(EventTestMixin, TestCase):
    """Test enabling/disabling self-generated certificates for a course. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    def setUp(self):  # pylint: disable=arguments-differ
        super(CertificateGenerationEnabledTest, self).setUp('certificates.api.tracker')

        # Since model-based configuration is cached, we need
        # to clear the cache before each test.
        cache.clear()

    @ddt.data(
        (None, None, False),
        (False, None, False),
        (False, True, False),
        (True, None, False),
        (True, False, False),
        (True, True, True)
    )
    @ddt.unpack
    def test_cert_generation_enabled(self, is_feature_enabled, is_course_enabled, expect_enabled):
        if is_feature_enabled is not None:
            CertificateGenerationConfiguration.objects.create(enabled=is_feature_enabled)

        if is_course_enabled is not None:
            certs_api.set_cert_generation_enabled(self.COURSE_KEY, is_course_enabled)
            cert_event_type = 'enabled' if is_course_enabled else 'disabled'
            event_name = '.'.join(['edx', 'certificate', 'generation', cert_event_type])
            self.assert_event_emitted(
                event_name,
                course_id=unicode(self.COURSE_KEY),
            )

        self._assert_enabled_for_course(self.COURSE_KEY, expect_enabled)

    def test_latest_setting_used(self):
        # Enable the feature
        CertificateGenerationConfiguration.objects.create(enabled=True)

        # Enable for the course
        certs_api.set_cert_generation_enabled(self.COURSE_KEY, True)
        self._assert_enabled_for_course(self.COURSE_KEY, True)

        # Disable for the course
        certs_api.set_cert_generation_enabled(self.COURSE_KEY, False)
        self._assert_enabled_for_course(self.COURSE_KEY, False)

    def test_setting_is_course_specific(self):
        # Enable the feature
        CertificateGenerationConfiguration.objects.create(enabled=True)

        # Enable for one course
        certs_api.set_cert_generation_enabled(self.COURSE_KEY, True)
        self._assert_enabled_for_course(self.COURSE_KEY, True)

        # Should be disabled for another course
        other_course = CourseLocator(org='other', course='other', run='other')
        self._assert_enabled_for_course(other_course, False)

    def _assert_enabled_for_course(self, course_key, expect_enabled):
        """Check that self-generated certificates are enabled or disabled for the course. """
        actual_enabled = certs_api.cert_generation_enabled(course_key)
        self.assertEqual(expect_enabled, actual_enabled)


@attr('shard_1')
class GenerateExampleCertificatesTest(TestCase):
    """Test generation of example certificates. """

    COURSE_KEY = CourseLocator(org='test', course='test', run='test')

    def setUp(self):
        super(GenerateExampleCertificatesTest, self).setUp()

    def test_generate_example_certs(self):
        # Generate certificates for the course
        CourseModeFactory.create(course_id=self.COURSE_KEY, mode_slug=CourseMode.HONOR)
        with self._mock_xqueue() as mock_queue:
            certs_api.generate_example_certificates(self.COURSE_KEY)

        # Verify that the appropriate certs were added to the queue
        self._assert_certs_in_queue(mock_queue, 1)

        # Verify that the certificate status is "started"
        self._assert_cert_status({
            'description': 'honor',
            'status': 'started'
        })

    def test_generate_example_certs_with_verified_mode(self):
        # Create verified and honor modes for the course
        CourseModeFactory(course_id=self.COURSE_KEY, mode_slug='honor')
        CourseModeFactory(course_id=self.COURSE_KEY, mode_slug='verified')

        # Generate certificates for the course
        with self._mock_xqueue() as mock_queue:
            certs_api.generate_example_certificates(self.COURSE_KEY)

        # Verify that the appropriate certs were added to the queue
        self._assert_certs_in_queue(mock_queue, 2)

        # Verify that the certificate status is "started"
        self._assert_cert_status(
            {
                'description': 'verified',
                'status': 'started'
            },
            {
                'description': 'honor',
                'status': 'started'
            }
        )

    @contextmanager
    def _mock_xqueue(self):
        """Mock the XQueue method for adding a task to the queue. """
        with patch.object(XQueueCertInterface, 'add_example_cert') as mock_queue:
            yield mock_queue

    def _assert_certs_in_queue(self, mock_queue, expected_num):
        """Check that the certificate generation task was added to the queue. """
        certs_in_queue = [call_args[0] for (call_args, __) in mock_queue.call_args_list]
        self.assertEqual(len(certs_in_queue), expected_num)
        for cert in certs_in_queue:
            self.assertTrue(isinstance(cert, ExampleCertificate))

    def _assert_cert_status(self, *expected_statuses):
        """Check the example certificate status. """
        actual_status = certs_api.example_certificates_status(self.COURSE_KEY)
        self.assertEqual(list(expected_statuses), actual_status)
