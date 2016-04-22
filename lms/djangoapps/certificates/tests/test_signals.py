"""
Unit tests for enabling self-generated certificates by default
for a self-paced courses.
"""
import unittest

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from certificates import api as certs_api
from certificates.models import CertificateGenerationConfiguration
from certificates.signals import _listen_for_course_publish


@unittest.skip("Fix this - getting unreliable query counts")
class EnableCertGenerationSignalTest(ModuleStoreTestCase):
    """
    Tests for enabling self-generated certificates by default
    for a self-paced courses.
    """

    def setUp(self):
        super(EnableCertGenerationSignalTest, self).setUp()
        self.course = CourseFactory.create(self_paced=True)
        # Enable the feature
        CertificateGenerationConfiguration.objects.create(enabled=True)

    def test_cert_generation_enabled_for_self_paced(self):
        """
        Verify the signal enable the self-generated certificates by default for
        self-paced courses.
        """
        self.assertFalse(certs_api.cert_generation_enabled(self.course.id))

        _listen_for_course_publish('store', self.course.id)
        self.assertTrue(certs_api.cert_generation_enabled(self.course.id))
