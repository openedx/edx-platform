"""
Unit tests for enabling self-generated certificates for self-paced courses
and disabling for instructor-paced courses.
"""


import ddt
import mock
import six
from edx_toggles.toggles import LegacyWaffleSwitch
from edx_toggles.toggles.testutils import override_waffle_flag
from edx_toggles.toggles.testutils import override_waffle_switch
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from lms.djangoapps.certificates.api import cert_generation_enabled
from lms.djangoapps.certificates.generation_handler import CERTIFICATES_USE_ALLOWLIST
from lms.djangoapps.certificates.models import (
    CertificateGenerationConfiguration,
    CertificateStatuses,
    GeneratedCertificate
)
from lms.djangoapps.certificates.signals import _fire_ungenerated_certificate_task
from lms.djangoapps.certificates.tasks import CERTIFICATE_DELAY_SECONDS
from lms.djangoapps.certificates.tests.factories import CertificateWhitelistFactory
from lms.djangoapps.certificates.tests.factories import GeneratedCertificateFactory
from lms.djangoapps.grades.course_grade_factory import CourseGradeFactory
from lms.djangoapps.grades.tests.utils import mock_passing_grade
from lms.djangoapps.verify_student.models import IDVerificationAttempt, SoftwareSecurePhotoVerification
from openedx.core.djangoapps.certificates.config import waffle

AUTO_CERTIFICATE_GENERATION_SWITCH = LegacyWaffleSwitch(waffle.waffle(), waffle.AUTO_CERTIFICATE_GENERATION)


class SelfGeneratedCertsSignalTest(ModuleStoreTestCase):
    """
    Tests for enabling/disabling self-generated certificates according to course-pacing.
    """
    ENABLED_SIGNALS = ['course_published']

    def setUp(self):
        super().setUp()
        CertificateGenerationConfiguration.objects.create(enabled=True)

    def test_cert_generation_flag_on_pacing_toggle(self):
        """
        Verify that signal enables or disables self-generated certificates
        according to course-pacing.
        """
        course = CourseFactory.create(self_paced=False, emit_signals=True)
        assert not cert_generation_enabled(course.id)

        course.self_paced = True
        self.store.update_item(course, self.user.id)
        assert cert_generation_enabled(course.id)

        course.self_paced = False
        self.store.update_item(course, self.user.id)
        assert not cert_generation_enabled(course.id)


class WhitelistGeneratedCertificatesTest(ModuleStoreTestCase):
    """
    Tests for whitelisted student auto-certificate generation
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(self_paced=True)
        self.user = UserFactory.create()
        CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode="verified",
        )
        self.ip_course = CourseFactory.create(self_paced=False)
        CourseEnrollmentFactory(
            user=self.user,
            course_id=self.ip_course.id,
            is_active=True,
            mode="verified",
        )

    def test_cert_generation_on_whitelist_append_self_paced(self):
        """
        Verify that signal is sent, received, and fires task
        based on 'AUTO_CERTIFICATE_GENERATION' flag
        """
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=False):
                CertificateWhitelistFactory(
                    user=self.user,
                    course_id=self.course.id
                )
                mock_generate_certificate_apply_async.assert_not_called()
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                CertificateWhitelistFactory(
                    user=self.user,
                    course_id=self.course.id
                )
                mock_generate_certificate_apply_async.assert_called_with(
                    countdown=CERTIFICATE_DELAY_SECONDS,
                    kwargs={
                        'student': six.text_type(self.user.id),
                        'course_key': six.text_type(self.course.id),
                    }
                )

    def test_cert_generation_on_whitelist_append_instructor_paced(self):
        """
        Verify that signal is sent, received, and fires task
        based on 'AUTO_CERTIFICATE_GENERATION' flag
        """
        with mock.patch(
                'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
                return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=False):
                CertificateWhitelistFactory(
                    user=self.user,
                    course_id=self.ip_course.id
                )
                mock_generate_certificate_apply_async.assert_not_called()
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                CertificateWhitelistFactory(
                    user=self.user,
                    course_id=self.ip_course.id
                )
                mock_generate_certificate_apply_async.assert_called_with(
                    countdown=CERTIFICATE_DELAY_SECONDS,
                    kwargs={
                        'student': six.text_type(self.user.id),
                        'course_key': six.text_type(self.ip_course.id),
                    }
                )

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
    def test_fire_task_allowlist_enabled(self):
        """
        Test that the allowlist generation is invoked if the allowlist is enabled for a user on the list
        """
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with mock.patch(
                'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
                return_value=None
            ) as mock_generate_allowlist_task:
                with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                    CertificateWhitelistFactory(
                        user=self.user,
                        course_id=self.ip_course.id,
                        whitelist=True
                    )
                    mock_generate_certificate_apply_async.assert_not_called()
                    mock_generate_allowlist_task.assert_called_with(self.user, self.ip_course.id)

    def test_fire_task_allowlist_disabled(self):
        """
        Test that the normal logic is followed if the allowlist is disabled for a user on the list
        """
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with mock.patch(
                'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
                return_value=None
            ) as mock_generate_allowlist_task:
                with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                    CertificateWhitelistFactory(
                        user=self.user,
                        course_id=self.ip_course.id,
                        whitelist=True
                    )
                    mock_generate_certificate_apply_async.assert_called_with(
                        countdown=CERTIFICATE_DELAY_SECONDS,
                        kwargs={
                            'student': six.text_type(self.user.id),
                            'course_key': six.text_type(self.ip_course.id),
                        }
                    )
                    mock_generate_allowlist_task.assert_not_called()


class PassingGradeCertsTest(ModuleStoreTestCase):
    """
    Tests for certificate generation task firing on passing grade receipt
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(
            self_paced=True,
        )
        self.user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode="verified",
        )
        self.ip_course = CourseFactory.create(self_paced=False)
        self.ip_enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.ip_course.id,
            is_active=True,
            mode="verified",
        )
        attempt = SoftwareSecurePhotoVerification.objects.create(
            user=self.user,
            status='submitted'
        )
        attempt.approve()

    def test_cert_generation_on_passing_self_paced(self):
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                grade_factory = CourseGradeFactory()
                # Not passing
                grade_factory.update(self.user, self.course)
                mock_generate_certificate_apply_async.assert_not_called()
                # Certs fired after passing
                with mock_passing_grade():
                    grade_factory.update(self.user, self.course)
                    mock_generate_certificate_apply_async.assert_called_with(
                        countdown=CERTIFICATE_DELAY_SECONDS,
                        kwargs={
                            'student': six.text_type(self.user.id),
                            'course_key': six.text_type(self.course.id),
                        }
                    )

    def test_cert_generation_on_passing_instructor_paced(self):
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                grade_factory = CourseGradeFactory()
                # Not passing
                grade_factory.update(self.user, self.ip_course)
                mock_generate_certificate_apply_async.assert_not_called()
                # Certs fired after passing
                with mock_passing_grade():
                    grade_factory.update(self.user, self.ip_course)
                    mock_generate_certificate_apply_async.assert_called_with(
                        countdown=CERTIFICATE_DELAY_SECONDS,
                        kwargs={
                            'student': six.text_type(self.user.id),
                            'course_key': six.text_type(self.ip_course.id),
                        }
                    )

    def test_cert_already_generated(self):
        with mock.patch(
                'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
                return_value=None
        ) as mock_generate_certificate_apply_async:
            grade_factory = CourseGradeFactory()
            # Create the certificate
            GeneratedCertificateFactory(
                user=self.user,
                course_id=self.course.id,
                status=CertificateStatuses.downloadable
            )
            # Certs are not re-fired after passing
            with mock_passing_grade():
                grade_factory.update(self.user, self.course)
                mock_generate_certificate_apply_async.assert_not_called()

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
    def test_passing_grade_allowlist(self):
        with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
            # User who is not on the allowlist
            GeneratedCertificateFactory(
                user=self.user,
                course_id=self.course.id,
                status=CertificateStatuses.error
            )
            with mock_passing_grade():
                with mock.patch(
                    'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
                    return_value=None
                ) as mock_allowlist_task:
                    CourseGradeFactory().update(self.user, self.course)
                    mock_allowlist_task.assert_not_called()

            # User who is on the allowlist
            u = UserFactory.create()
            c = CourseFactory()
            course_key = c.id  # pylint: disable=no-member
            CertificateWhitelistFactory(
                user=u,
                course_id=course_key
            )
            GeneratedCertificateFactory(
                user=u,
                course_id=course_key,
                status=CertificateStatuses.error
            )
            with mock_passing_grade():
                with mock.patch(
                    'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
                    return_value=None
                ) as mock_allowlist_task:
                    CourseGradeFactory().update(u, c)
                    mock_allowlist_task.assert_called_with(u, course_key)


@ddt.ddt
class FailingGradeCertsTest(ModuleStoreTestCase):
    """
    Tests for marking certificate notpassing when grade goes from passing to failing,
    and that the signal has no effect on the cert status if the cert has a non-passing
    status
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create(
            self_paced=True,
        )
        self.user = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode="verified",
        )
        attempt = SoftwareSecurePhotoVerification.objects.create(
            user=self.user,
            status='submitted'
        )
        attempt.approve()

    @ddt.data(
        CertificateStatuses.deleted,
        CertificateStatuses.deleting,
        CertificateStatuses.downloadable,
        CertificateStatuses.error,
        CertificateStatuses.generating,
        CertificateStatuses.notpassing,
        CertificateStatuses.restricted,
        CertificateStatuses.unavailable,
        CertificateStatuses.auditing,
        CertificateStatuses.audit_passing,
        CertificateStatuses.audit_notpassing,
        CertificateStatuses.unverified,
        CertificateStatuses.invalidated,
        CertificateStatuses.requesting,
    )
    def test_cert_failure(self, status):
        if CertificateStatuses.is_passing_status(status):
            expected_status = CertificateStatuses.notpassing
        else:
            expected_status = status
        GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            status=status
        )
        CourseGradeFactory().update(self.user, self.course)
        cert = GeneratedCertificate.certificate_for_student(self.user, self.course.id)
        assert cert.status == expected_status

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
    def test_failing_grade_allowlist(self):
        # User who is not on the allowlist
        GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            status=CertificateStatuses.downloadable
        )
        CourseGradeFactory().update(self.user, self.course)
        cert = GeneratedCertificate.certificate_for_student(self.user, self.course.id)
        assert cert.status == CertificateStatuses.notpassing

        # User who is on the allowlist
        u = UserFactory.create()
        c = CourseFactory()
        course_key = c.id  # pylint: disable=no-member
        CertificateWhitelistFactory(
            user=u,
            course_id=course_key
        )
        GeneratedCertificateFactory(
            user=u,
            course_id=course_key,
            status=CertificateStatuses.downloadable
        )
        CourseGradeFactory().update(u, c)
        cert = GeneratedCertificate.certificate_for_student(u, course_key)
        assert cert.status == CertificateStatuses.downloadable


class LearnerTrackChangeCertsTest(ModuleStoreTestCase):
    """
    Tests for certificate generation task firing on learner verification
    """

    def setUp(self):
        super().setUp()
        self.course_one = CourseFactory.create(self_paced=True)
        self.user_one = UserFactory.create()
        self.enrollment_one = CourseEnrollmentFactory(
            user=self.user_one,
            course_id=self.course_one.id,
            is_active=True,
            mode='verified',
        )
        self.user_two = UserFactory.create()
        self.course_two = CourseFactory.create(self_paced=False)
        self.enrollment_two = CourseEnrollmentFactory(
            user=self.user_two,
            course_id=self.course_two.id,
            is_active=True,
            mode='verified'
        )
        with mock_passing_grade():
            grade_factory = CourseGradeFactory()
            grade_factory.update(self.user_one, self.course_one)
            grade_factory.update(self.user_two, self.course_two)

    def test_cert_generation_on_photo_verification_self_paced(self):
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                mock_generate_certificate_apply_async.assert_not_called()
                attempt = SoftwareSecurePhotoVerification.objects.create(
                    user=self.user_one,
                    status='submitted'
                )
                attempt.approve()
                mock_generate_certificate_apply_async.assert_called_with(
                    countdown=CERTIFICATE_DELAY_SECONDS,
                    kwargs={
                        'student': six.text_type(self.user_one.id),
                        'course_key': six.text_type(self.course_one.id),
                        'expected_verification_status': IDVerificationAttempt.STATUS.approved,
                    }
                )

    def test_cert_generation_on_photo_verification_instructor_paced(self):
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                mock_generate_certificate_apply_async.assert_not_called()
                attempt = SoftwareSecurePhotoVerification.objects.create(
                    user=self.user_two,
                    status='submitted'
                )
                attempt.approve()
                mock_generate_certificate_apply_async.assert_called_with(
                    countdown=CERTIFICATE_DELAY_SECONDS,
                    kwargs={
                        'student': six.text_type(self.user_two.id),
                        'course_key': six.text_type(self.course_two.id),
                        'expected_verification_status': IDVerificationAttempt.STATUS.approved,
                    }
                )

    @override_waffle_flag(CERTIFICATES_USE_ALLOWLIST, active=True)
    def test_id_verification_allowlist(self):
        # User is not on the allowlist
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
            return_value=None
        ) as mock_allowlist_task:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                attempt = SoftwareSecurePhotoVerification.objects.create(
                    user=self.user_two,
                    status='submitted'
                )
                attempt.approve()
                mock_allowlist_task.assert_not_called()

        # User is on the allowlist
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_allowlist_certificate_task',
            return_value=None
        ) as mock_allowlist_task:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                u = UserFactory.create()
                c = CourseFactory()
                course_key = c.id  # pylint: disable=no-member
                CourseEnrollmentFactory(
                    user=u,
                    course_id=course_key,
                    is_active=True,
                    mode='verified'
                )
                CertificateWhitelistFactory(
                    user=u,
                    course_id=course_key
                )
                attempt = SoftwareSecurePhotoVerification.objects.create(
                    user=u,
                    status='submitted'
                )
                attempt.approve()
                mock_allowlist_task.assert_called_with(u, course_key)


@ddt.ddt
class CertificateGenerationTaskTest(ModuleStoreTestCase):
    """
    Tests for certificate generation task.
    """

    def setUp(self):
        super().setUp()
        self.course = CourseFactory.create()

    @ddt.data(
        ('professional', True),
        ('verified', True),
        ('no-id-professional', True),
        ('credit', True),
        ('masters', True),
        ('audit', False),
        ('honor', False),
    )
    @ddt.unpack
    def test_fire_ungenerated_certificate_task_allowed_modes(self, enrollment_mode, should_create):
        """
        Test that certificate generation task is fired for only modes that are
        allowed to generate certificates automatically.
        """
        self.user = UserFactory.create()
        CourseEnrollmentFactory(
            user=self.user,
            course_id=self.course.id,
            is_active=True,
            mode=enrollment_mode
        )
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with override_waffle_switch(AUTO_CERTIFICATE_GENERATION_SWITCH, active=True):
                _fire_ungenerated_certificate_task(self.user, self.course.id)
                task_created = mock_generate_certificate_apply_async.called
                assert task_created == should_create
