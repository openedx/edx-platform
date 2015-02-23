"""
Tests for the certificates api and helper function.
"""
from django.test import RequestFactory
from django.test.utils import override_settings
from mock import patch, Mock
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from certificates.api import certificate_downloadable_status, generate_user_certificates
from student.models import CourseEnrollment

from student.tests.factories import UserFactory
from certificates.models import CertificateStatuses
from certificates.tests.factories import GeneratedCertificateFactory


class CertificateDownloadableStatusTests(ModuleStoreTestCase):
    """
    Tests for the certificate_downloadable_status helper function
    """

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

    def test_user_cert_status_with_generating(self):
        """
        in case of certificate with error means means is_generating is True and is_downloadable is False
        """
        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.generating,
            mode='verified'
        )

        self.assertEqual(
            certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': True,
                'download_url': None
            }
        )

    def test_user_cert_status_with_error(self):
        """
        in case of certificate with error means means is_generating is True and is_downloadable is False
        """

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.error,
            mode='verified'
        )

        self.assertEqual(
            certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': True,
                'download_url': None
            }
        )

    def test_user_with_out_cert(self):
        """
        in case of no certificate means is_generating is False and is_downloadable is False
        """
        self.assertEqual(
            certificate_downloadable_status(self.student_no_cert, self.course.id),
            {
                'is_downloadable': False,
                'is_generating': False,
                'download_url': None
            }
        )

    def test_user_with_downloadable_cert(self):
        """
        in case of downloadable certificate means is_generating is False and is_downloadable is True
        download_url has cert link
        """

        GeneratedCertificateFactory.create(
            user=self.student,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable,
            mode='verified',
            download_url='www.google.com'
        )

        self.assertEqual(
            certificate_downloadable_status(self.student, self.course.id),
            {
                'is_downloadable': True,
                'is_generating': False,
                'download_url': 'www.google.com'
            }
        )


class GenerateUserCertificatesTest(ModuleStoreTestCase):
    """
    Tests for the generate_user_certificates helper function
    """

    def setUp(self):
        super(GenerateUserCertificatesTest, self).setUp()

        self.student = UserFactory()
        self.student_no_cert = UserFactory()
        self.course = CourseFactory.create(
            org='edx',
            number='verified',
            display_name='Verified Course',
            grade_cutoffs={'cutoff': 0.75, 'Pass': 0.5}
        )
        self.enrollment = CourseEnrollment.enroll(self.student, self.course.id, mode='honor')
        self.request_factory = RequestFactory()

    @override_settings(CERT_QUEUE='certificates')
    @patch('courseware.grades.grade', Mock(return_value={'grade': 'Pass', 'percent': 0.75}))
    def test_new_cert_requests_into_xqueue_returns_generating(self):
        """
        mocking grade.grade and returns a summary with passing score.
        new requests saves into xqueue and returns the status
        """
        with patch('capa.xqueue_interface.XQueueInterface.send_to_queue') as mock_send_to_queue:
            mock_send_to_queue.return_value = (0, "Successfully queued")
            self.assertEqual(generate_user_certificates(self.student, self.course), 'generating')
