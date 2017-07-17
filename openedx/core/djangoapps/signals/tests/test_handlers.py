"""
Unit tests for enabling self-generated certificates for self-paced courses
and disabling for instructor-paced courses.
"""

from certificates import api as certs_api
from certificates.models import CertificateGenerationConfiguration
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from openedx.core.djangoapps.signals.handlers import _listen_for_course_pacing_changed


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
