"""
Tests for the certificates models.
"""

from django.test import TestCase

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from student.tests.factories import UserFactory
from certificates.models import CertificateStatuses, GeneratedCertificate, certificate_status_for_student


class CertificatesModelTest(ModuleStoreTestCase):
    """
    Tests for the GeneratedCertificate model
    """

    def test_certificate_status_for_student(self):
        student = UserFactory()
        course = CourseFactory.create(org='edx', number='verified', display_name='Verified Course')

        certificate_status = certificate_status_for_student(student, course.id)
        self.assertEqual(certificate_status['status'], CertificateStatuses.unavailable)
        self.assertEqual(certificate_status['mode'], GeneratedCertificate.MODES.honor)
