"""
Tests for the cert_generation command
"""

from unittest import mock

import pytest
from django.core.management import CommandError, call_command

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.modulestore.tests.factories import CourseFactory  # lint-amnesty, pylint: disable=wrong-import-order

COMMAND_INTEGRITY_ENABLED = \
    'lms.djangoapps.certificates.management.commands.regenerate_noidv_cert.is_integrity_signature_enabled'
INTEGRITY_ENABLED_METHOD = 'lms.djangoapps.certificates.generation_handler.is_integrity_signature_enabled'
ID_VERIFIED_METHOD = 'lms.djangoapps.verify_student.services.IDVerificationService.user_is_verified'
PASSING_GRADE_METHOD = 'lms.djangoapps.certificates.generation_handler._is_passing_grade'
WEB_CERTS_METHOD = 'lms.djangoapps.certificates.generation_handler.has_html_certificates_enabled'


# base setup is unverified users, honor code (integrity) turned on wherever imports it
# and normal passing grade certificates for convenience
@mock.patch(ID_VERIFIED_METHOD, mock.Mock(return_value=False))
@mock.patch(INTEGRITY_ENABLED_METHOD, mock.Mock(return_value=True))
@mock.patch(COMMAND_INTEGRITY_ENABLED, mock.Mock(return_value=True))
@mock.patch(PASSING_GRADE_METHOD, mock.Mock(return_value=True))
@mock.patch(WEB_CERTS_METHOD, mock.Mock(return_value=True))
class RegenerateNoIDVCertTests(ModuleStoreTestCase):
    """
    Tests for the regenerate_noidv_cert management command
    """

    def test_command_with_missing_param_course_key(self):
        """
        Verify command with a missing param -- course key.
        """
        with pytest.raises(CommandError, match="You must specify a course-key or keys"):
            call_command("regenerate_noidv_cert")

    def test_command_with_invalid_key(self):
        """
        Verify command with an invalid course run key
        """
        with pytest.raises(CommandError, match=" is not a valid course-key"):
            call_command("regenerate_noidv_cert", "-c", "blah")

    def test_regeneration(self):
        """
        Single regeneration base case
        """
        course_run = CourseFactory()
        course_run_key = course_run.id

        user = UserFactory()
        CourseEnrollmentFactory(
            user=user,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.unverified
        )

        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key)
        self.assertEqual('1', regenerated)

    def test_regeneration_verified(self):
        """
        Only unverified certificates should get regenerated
        """
        course_run = CourseFactory()
        course_run_key = course_run.id

        user = UserFactory()
        CourseEnrollmentFactory(
            user=user,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.downloadable
        )

        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key)
        self.assertEqual('0', regenerated)

    def test_regeneration_honor_off(self):
        """
        If a course does not have the honor code enabled, no point regenerating
        """
        course_run = CourseFactory()
        course_run_key = course_run.id

        user = UserFactory()
        CourseEnrollmentFactory(
            user=user,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.unverified
        )

        with mock.patch(COMMAND_INTEGRITY_ENABLED, mock.Mock(return_value=False)):
            regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key)
            self.assertEqual('0', regenerated)

    def _multisetup(self):
        """
        setup certs across two course runs
        """
        course_run = CourseFactory()
        course_run_key = course_run.id
        course_run2 = CourseFactory()
        course_run_key2 = course_run2.id

        user = UserFactory()
        CourseEnrollmentFactory(
            user=user,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.unverified
        )

        user1 = UserFactory()
        CourseEnrollmentFactory(
            user=user1,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user1,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.unverified
        )

        user2 = UserFactory()
        CourseEnrollmentFactory(
            user=user2,
            course_id=course_run_key2,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user2,
            course_id=course_run_key2,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.unverified
        )

        user_verified = UserFactory()
        CourseEnrollmentFactory(
            user=user_verified,
            course_id=course_run_key,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user_verified,
            course_id=course_run_key,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.downloadable
        )

        user_failing = UserFactory()
        CourseEnrollmentFactory(
            user=user_failing,
            course_id=course_run_key2,
            is_active=True,
            mode=CourseMode.VERIFIED,
        )
        GeneratedCertificateFactory(
            user=user_failing,
            course_id=course_run_key2,
            mode=GeneratedCertificate.MODES.verified,
            status=CertificateStatuses.notpassing
        )
        return (course_run_key, course_run_key2)

    def test_multiple_regeneration(self):
        """
        Verify regeneration across multiple courses and users
        """
        course_run_key, course_run_key2 = self._multisetup()

        #3/5 in unverified status
        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key, course_run_key2)
        self.assertEqual('3', regenerated)

        #nothing left unverified for another run
        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key, course_run_key2)
        self.assertEqual('0', regenerated)

    def test_course_at_a_time(self):
        """
        Verify course regeneration separated
        """
        course_run_key, course_run_key2 = self._multisetup()

        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key)
        self.assertEqual('2', regenerated)

        regenerated = call_command("regenerate_noidv_cert", "-c", course_run_key2)
        self.assertEqual('1', regenerated)
