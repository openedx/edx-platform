"""
Tests for certificate generation
"""
import logging

from edx_toggles.toggles import LegacyWaffleSwitch
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from common.djangoapps.util.testing import EventTestMixin
from lms.djangoapps.certificates.generation import generate_allowlist_certificate
from lms.djangoapps.certificates.models import GeneratedCertificate, CertificateStatuses
from openedx.core.djangoapps.certificates.config import waffle

log = logging.getLogger(__name__)

ID_VERIFIED_METHOD = 'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
AUTO_GENERATION_NAMESPACE = waffle.WAFFLE_NAMESPACE
AUTO_GENERATION_NAME = waffle.AUTO_CERTIFICATE_GENERATION
AUTO_GENERATION_SWITCH_NAME = '{}.{}'.format(AUTO_GENERATION_NAMESPACE, AUTO_GENERATION_NAME)
AUTO_GENERATION_SWITCH = LegacyWaffleSwitch(AUTO_GENERATION_NAMESPACE, AUTO_GENERATION_NAME)


class AllowlistTests(EventTestMixin, ModuleStoreTestCase):
    """
    Tests for generating allowlist certificates
    """

    def setUp(self):  # pylint: disable=arguments-differ
        super().setUp('lms.djangoapps.certificates.utils.tracker')

    def test_allowlist_generation(self):
        """
        Test allowlist certificate generation
        """
        # Create user, a course run, and an enrollment
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=u,
            course_id=key,
            is_active=True,
            mode="verified",
        )

        certs = GeneratedCertificate.objects.filter(user=u, course_id=key)
        assert len(certs) == 0

        generated_cert = generate_allowlist_certificate(u, key)
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
            generation_mode='batch'
        )
