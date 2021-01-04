"""
Unit Tests for the Certificate service
"""


from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.services import CertificateService
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CertificateServiceTests(ModuleStoreTestCase):
    """
    Tests for the Certificate service
    """

    def setUp(self):
        super(CertificateServiceTests, self).setUp()
        self.service = CertificateService()
        self.course = CourseFactory()
        self.user = UserFactory()
        self.user_id = self.user.id
        self.course_id = self.course.id
        GeneratedCertificateFactory.create(
            status=CertificateStatuses.downloadable,
            user=self.user,
            course_id=self.course.id,
            grade=1.0
        )

    def generated_certificate_to_dict(self, generated_certificate):
        """
        Converts a Generated Certificate instance to a Python dictionary
        """
        return {
            'verify_uuid': generated_certificate.verify_uuid,
            'download_uuid': generated_certificate.download_uuid,
            'download_url': generated_certificate.download_url,
            'grade': generated_certificate.grade,
            'status': generated_certificate.status
        }

    def test_invalidate_certificate(self):
        """
        Verify that CertificateService invalidates the user certificate
        """
        self.service.invalidate_certificate(self.user_id, self.course_id)
        invalid_generated_certificate = GeneratedCertificate.objects.get(
            user=self.user_id,
            course_id=self.course_id
        )
        self.assertDictEqual(
            self.generated_certificate_to_dict(invalid_generated_certificate),
            {
                'verify_uuid': '',
                'download_uuid': '',
                'download_url': '',
                'grade': '',
                'status': CertificateStatuses.unavailable
            }
        )
