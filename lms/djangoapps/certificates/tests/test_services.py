"""
Unit Tests for the Certificate service
"""

from edx_toggles.toggles.testutils import override_waffle_flag
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.certificates.generation_handler import CERTIFICATES_USE_ALLOWLIST
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.services import CertificateService
from lms.djangoapps.certificates.tests.factories import CertificateWhitelistFactory
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory


class CertificateServiceTests(ModuleStoreTestCase):
    """
    Tests for the Certificate service
    """

    def setUp(self):
        super().setUp()
        self.service = CertificateService()
        self.course = CourseFactory()
        self.user = UserFactory()
        self.user_id = self.user.id
        self.course_id = self.course.id  # pylint: disable=no-member
        GeneratedCertificateFactory.create(
            status=CertificateStatuses.downloadable,
            user=self.user,
            course_id=self.course.id,  # pylint: disable=no-member
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
        success = self.service.invalidate_certificate(self.user_id, self.course_id)
        assert success

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

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
    def test_invalidate_certificate_allowlist(self):
        """
        Verify that CertificateService does not invalidate the certificate if it is allowlisted
        """
        u = UserFactory.create()
        c = CourseFactory()
        course_key = c.id  # pylint: disable=no-member
        GeneratedCertificateFactory.create(
            status=CertificateStatuses.downloadable,
            user=u,
            course_id=course_key,
            grade=1.0
        )
        CertificateWhitelistFactory(
            user=u,
            course_id=course_key
        )
        success = self.service.invalidate_certificate(u.id, course_key)
        assert not success

        cert = GeneratedCertificate.objects.get(user=u.id, course_id=course_key)
        assert cert.status == CertificateStatuses.downloadable
