"""
Tests for certificate generation handler
"""
import logging

import ddt
import mock
from edx_toggles.toggles import LegacyWaffleSwitch
from edx_toggles.toggles.testutils import override_waffle_flag
from edx_toggles.toggles.testutils import override_waffle_switch
from waffle.testutils import override_switch
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.generation_handler import CERTIFICATES_USE_ALLOWLIST
from lms.djangoapps.certificates.generation_handler import _is_using_certificate_allowlist, \
    _can_generate_allowlist_certificate_for_status, generate_allowlist_certificate_task, \
    can_generate_allowlist_certificate
from lms.djangoapps.certificates.models import GeneratedCertificate, CertificateStatuses
from lms.djangoapps.certificates.tests.factories import CertificateWhitelistFactory, GeneratedCertificateFactory, \
    CertificateInvalidationFactory
from openedx.core.djangoapps.certificates.config import waffle

log = logging.getLogger(__name__)

ID_VERIFIED_METHOD = 'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
AUTO_GENERATION_NAMESPACE = waffle.WAFFLE_NAMESPACE
AUTO_GENERATION_NAME = waffle.AUTO_CERTIFICATE_GENERATION
AUTO_GENERATION_SWITCH_NAME = '{}.{}'.format(AUTO_GENERATION_NAMESPACE, AUTO_GENERATION_NAME)
AUTO_GENERATION_SWITCH = LegacyWaffleSwitch(AUTO_GENERATION_NAMESPACE, AUTO_GENERATION_NAME)


@override_switch(AUTO_GENERATION_SWITCH_NAME, active=True)
@override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
@mock.patch(ID_VERIFIED_METHOD, mock.Mock(return_value=True))
@ddt.ddt
class AllowlistTests(ModuleStoreTestCase):
    """
    Tests for handling allowlist certificates
    """

    def setUp(self):
        super().setUp()

        # Create user, a course run, and an enrollment
        self.user = UserFactory()
        self.course_run = CourseFactory()
        self.course_run_key = self.course_run.id  # pylint: disable=no-member
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course_run_key,
            is_active=True,
            mode="verified",
        )

        # Whitelist user
        CertificateWhitelistFactory.create(course_id=self.course_run_key, user=self.user)

    def test_is_using_allowlist_true(self):
        """
        Test the allowlist flag
        """
        self.assertTrue(_is_using_certificate_allowlist(self.course_run_key))

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=False)
    def test_is_using_allowlist_false(self):
        """
        Test the allowlist flag without the override
        """
        self.assertFalse(_is_using_certificate_allowlist(self.course_run_key))

    @ddt.data(
        (CertificateStatuses.deleted, True),
        (CertificateStatuses.deleting, True),
        (CertificateStatuses.downloadable, False),
        (CertificateStatuses.error, True),
        (CertificateStatuses.generating, True),
        (CertificateStatuses.notpassing, True),
        (CertificateStatuses.restricted, True),
        (CertificateStatuses.unavailable, True),
        (CertificateStatuses.audit_passing, True),
        (CertificateStatuses.audit_notpassing, True),
        (CertificateStatuses.honor_passing, True),
        (CertificateStatuses.unverified, True),
        (CertificateStatuses.invalidated, True),
        (CertificateStatuses.requesting, True))
    @ddt.unpack
    def test_generation_status(self, status, expected_response):
        """
        Test handling of certificate statuses
        """
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        cert = GeneratedCertificateFactory(
            user=u,
            course_id=key,
            mode=GeneratedCertificate.MODES.verified,
            status=status,
        )

        self.assertEqual(_can_generate_allowlist_certificate_for_status(cert), expected_response)

    def test_generation_status_for_none(self):
        """
        Test handling of certificate statuses for a non-existent cert
        """
        self.assertEqual(_can_generate_allowlist_certificate_for_status(None), True)

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=False)
    def test_handle_invalid(self):
        """
        Test handling of an invalid user/course run combo
        """
        self.assertFalse(can_generate_allowlist_certificate(self.user, self.course_run_key))
        self.assertFalse(generate_allowlist_certificate_task(self.user, self.course_run_key))

    def test_handle_valid(self):
        """
        Test handling of a valid user/course run combo
        """
        self.assertTrue(can_generate_allowlist_certificate(self.user, self.course_run_key))
        self.assertTrue(generate_allowlist_certificate_task(self.user, self.course_run_key))

    def test_can_generate_auto_disabled(self):
        """
        Test handling when automatic generation is disabled
        """
        with override_waffle_switch(AUTO_GENERATION_SWITCH, active=False):
            self.assertFalse(can_generate_allowlist_certificate(self.user, self.course_run_key))

    def test_can_generate_not_verified(self):
        """
        Test handling when the user's id is not verified
        """
        with mock.patch(ID_VERIFIED_METHOD, return_value=False):
            self.assertFalse(can_generate_allowlist_certificate(self.user, self.course_run_key))

    def test_can_generate_not_enrolled(self):
        """
        Test handling when user is not enrolled
        """
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CertificateWhitelistFactory.create(course_id=key, user=u)
        self.assertFalse(can_generate_allowlist_certificate(u, key))

    def test_can_generate_not_whitelisted(self):
        """
        Test handling when user is not whitelisted
        """
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=u,
            course_id=key,
            is_active=True,
            mode="verified",
        )
        self.assertFalse(can_generate_allowlist_certificate(u, key))

    def test_can_generate_invalidated(self):
        """
        Test handling when user is on the invalidate list
        """
        u = UserFactory()
        cr = CourseFactory()
        key = cr.id  # pylint: disable=no-member
        CourseEnrollmentFactory(
            user=u,
            course_id=key,
            is_active=True,
            mode="verified",
        )
        cert = GeneratedCertificateFactory(
            user=u,
            course_id=key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.downloadable
        )
        CertificateWhitelistFactory.create(course_id=key, user=u)
        CertificateInvalidationFactory.create(
            generated_certificate=cert,
            invalidated_by=self.user,
            active=True
        )

        self.assertFalse(can_generate_allowlist_certificate(u, key))
