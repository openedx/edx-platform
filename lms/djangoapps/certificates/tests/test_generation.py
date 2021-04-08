"""
Tests for certificate generation
"""
import logging

from edx_toggles.toggles import LegacyWaffleSwitch

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.testing import EventTestMixin
from lms.djangoapps.certificates.generation import generate_course_certificate
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from openedx.core.djangoapps.certificates.config import waffle
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

log = logging.getLogger(__name__)

ID_VERIFIED_METHOD = 'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
AUTO_GENERATION_NAMESPACE = waffle.WAFFLE_NAMESPACE
AUTO_GENERATION_NAME = waffle.AUTO_CERTIFICATE_GENERATION
AUTO_GENERATION_SWITCH_NAME = f'{AUTO_GENERATION_NAMESPACE}.{AUTO_GENERATION_NAME}'
AUTO_GENERATION_SWITCH = LegacyWaffleSwitch(AUTO_GENERATION_NAMESPACE, AUTO_GENERATION_NAME)


class CertificateTests(EventTestMixin, ModuleStoreTestCase):
    """
    Tests for certificate generation
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp('lms.djangoapps.certificates.utils.tracker')

    def test_generation(self):
        """
        Test certificate generation
        """
        # Create user, a course run, and an enrollment
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=u,
            course_id=key,
            is_active=True,
            mode='verified',
        )
        gen_mode = 'batch'

        certs = GeneratedCertificate.objects.filter(user=u, course_id=key)
        assert len(certs) == 0

        generated_cert = generate_course_certificate(u, key, gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable

        certs = GeneratedCertificate.objects.filter(user=u, course_id=key)
        assert len(certs) == 1

        self.assert_event_emitted(
            'edx.certificate.created',
            user_id=u.id,
            course_id=str(key),
            certificate_id=generated_cert.verify_uuid,
            enrollment_mode=generated_cert.mode,
            certificate_url='',
            generation_mode=gen_mode
        )

    def test_generation_existing(self):
        """
        Test certificate generation when a certificate already exists
        """
        # Create user, a course run, and an enrollment
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=u,
            course_id=key,
            is_active=True,
            mode='verified',
        )
        error_reason = 'Some PDF error'
        GeneratedCertificateFactory(
            user=u,
            course_id=key,
            mode='verified',
            status=CertificateStatuses.error,
            error_reason=error_reason
        )
        gen_mode = 'batch'

        cert = GeneratedCertificate.objects.get(user=u, course_id=key)
        assert cert.error_reason == error_reason

        generated_cert = generate_course_certificate(u, key, gen_mode)
        assert generated_cert.status, CertificateStatuses.downloadable

        cert = GeneratedCertificate.objects.get(user=u, course_id=key)
        assert cert.error_reason == ''
