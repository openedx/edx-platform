"""
Tests for certificate generation
"""
import logging

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.testing import EventTestMixin
from lms.djangoapps.certificates.generation import generate_course_certificate
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)


class CertificateTests(EventTestMixin, ModuleStoreTestCase):
    """
    Tests for certificate generation
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp('lms.djangoapps.certificates.utils.tracker')

        # Create user, a course run, and an enrollment
        self.u = UserFactory()
        self.cr = CourseFactory()
        self.key = self.cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=self.u,
            course_id=self.key,
            is_active=True,
            mode='verified',
        )
        self.gen_mode = 'batch'

    def test_generation(self):
        """
        Test certificate generation
        """
        certs = GeneratedCertificate.objects.filter(user=self.u, course_id=self.key)
        assert len(certs) == 0

        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable

        certs = GeneratedCertificate.objects.filter(user=self.u, course_id=self.key)
        assert len(certs) == 1

        self.assert_event_emitted(
            'edx.certificate.created',
            user_id=self.u.id,
            course_id=str(self.key),
            certificate_id=generated_cert.verify_uuid,
            enrollment_mode=generated_cert.mode,
            certificate_url='',
            generation_mode=self.gen_mode
        )

    def test_generation_existing(self):
        """
        Test certificate generation when a certificate already exists
        """
        error_reason = 'Some PDF error'
        GeneratedCertificateFactory(
            user=self.u,
            course_id=self.key,
            mode='verified',
            status=CertificateStatuses.error,
            error_reason=error_reason
        )

        cert = GeneratedCertificate.objects.get(user=self.u, course_id=self.key)
        assert cert.error_reason == error_reason

        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable

        cert = GeneratedCertificate.objects.get(user=self.u, course_id=self.key)
        assert cert.error_reason == ''

    def test_generation_uuid_persists_through_revocation(self):
        """
        Test that the `verify_uuid` value of a certificate does not change when it is revoked and re-awarded.
        """
        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable

        verify_uuid = generated_cert.verify_uuid

        generated_cert.invalidate()
        assert generated_cert.status, CertificateStatuses.unavailable
        assert generated_cert.verify_uuid, verify_uuid

        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable
        assert generated_cert.verify_uuid, verify_uuid

        generated_cert.mark_notpassing(50.00)
        assert generated_cert.status, CertificateStatuses.notpassing
        assert generated_cert.verify_uuid, verify_uuid

        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable
        assert generated_cert.verify_uuid, verify_uuid

    def test_generation_creates_verify_uuid_when_needed(self):
        """
        Test that ensures we will create a verify_uuid when needed.
        """
        GeneratedCertificateFactory(
            user=self.u,
            course_id=self.key,
            mode='verified',
            status=CertificateStatuses.unverified,
            verify_uuid=''
        )

        generated_cert = generate_course_certificate(self.u, self.key, self.gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable
        assert generated_cert.verify_uuid != ''
