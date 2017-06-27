"""
Unit tests for enabling self-generated certificates for self-paced courses
and disabling for instructor-paced courses.
"""
import mock

from certificates import api as certs_api
from certificates.config import waffle
from certificates.models import CertificateGenerationConfiguration, CertificateWhitelist
from certificates.signals import _listen_for_course_pacing_changed
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class SelfGeneratedCertsSignalTest(ModuleStoreTestCase):
    """
    Tests for enabling/disabling self-generated certificates according to course-pacing.
    """

    def setUp(self):
        super(SelfGeneratedCertsSignalTest, self).setUp()
        SelfPacedConfiguration(enabled=True).save()
        self.course = CourseFactory.create(self_paced=True)
        # Enable the feature
        CertificateGenerationConfiguration.objects.create(enabled=True)

    def test_cert_generation_flag_on_pacing_toggle(self):
        """
        Verify that signal enables or disables self-generated certificates
        according to course-pacing.
        """
        #self-generation of cert disables by default
        self.assertFalse(certs_api.cert_generation_enabled(self.course.id))

        _listen_for_course_pacing_changed('store', self.course.id, self.course.self_paced)
        #verify that self-generation of cert is enabled for self-paced course
        self.assertTrue(certs_api.cert_generation_enabled(self.course.id))

        self.course.self_paced = False
        self.store.update_item(self.course, self.user.id)

        _listen_for_course_pacing_changed('store', self.course.id, self.course.self_paced)
        # verify that self-generation of cert is disabled for instructor-paced course
        self.assertFalse(certs_api.cert_generation_enabled(self.course.id))


class WhitelistGeneratedCertificatesTest(ModuleStoreTestCase):
    """
    Tests for whitelisted student auto-certificate generation
    """
    def setUp(self):
        super(WhitelistGeneratedCertificatesTest, self).setUp()
        self.course = CourseFactory.create(self_paced=True)
        self.user = UserFactory.create()
        self.ip_course = CourseFactory.create(self_paced=False)

    def test_cert_generation_on_whitelist_append(self):
        """
        Verify that signal is sent, received, and fires task based on various flag configs
        """
        with mock.patch(
            'lms.djangoapps.certificates.signals.generate_certificate.apply_async',
            return_value=None
        ) as mock_generate_certificate_apply_async:
            with waffle.waffle().override(waffle.SELF_PACED_ONLY, active=False):
                CertificateWhitelist.objects.create(
                    user=self.user,
                    course_id=self.course.id
                )
                mock_generate_certificate_apply_async.assert_not_called(
                    student=self.user,
                    course_key=self.course.id
                )
            with waffle.waffle().override(waffle.SELF_PACED_ONLY, active=True):
                CertificateWhitelist.objects.create(
                    user=self.user,
                    course_id=self.course.id
                )
                mock_generate_certificate_apply_async.assert_called_with(
                    student=self.user,
                    course_key=self.course.id,
                )
            with waffle.waffle().override(waffle.INSTRUCTOR_PACED_ONLY, active=False):
                CertificateWhitelist.objects.create(
                    user=self.user,
                    course_id=self.ip_course.id
                )
                mock_generate_certificate_apply_async.assert_not_called(
                    student=self.user,
                    course_key=self.ip_course.id
                )
            with waffle.waffle().override(waffle.INSTRUCTOR_PACED_ONLY, active=True):
                CertificateWhitelist.objects.create(
                    user=self.user,
                    course_id=self.ip_course.id
                )
                mock_generate_certificate_apply_async.assert_called_with(
                    student=self.user,
                    course_key=self.ip_course.id
                )
