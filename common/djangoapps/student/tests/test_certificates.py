"""Tests for display of certificates on the student dashboard. """

import unittest
import ddt

from django.conf import settings
from django.core.urlresolvers import reverse

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CertificateDisplayTest(ModuleStoreTestCase):
    """Tests display of certificates on the student dashboard. """

    USERNAME = "test_user"
    PASSWORD = "password"
    DOWNLOAD_URL = "http://www.example.com/certificate.pdf"

    def setUp(self):
        super(CertificateDisplayTest, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

        self.course = CourseFactory()
        self.course.certificates_display_behavior = "early_with_info"
        self.update_course(self.course, self.user.username)

    @ddt.data('verified', 'professional')
    def test_display_verified_certificate(self, enrollment_mode):
        self._create_certificate(enrollment_mode)
        self._check_can_download_certificate()

    def _create_certificate(self, enrollment_mode):
        """Simulate that the user has a generated certificate. """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, mode=enrollment_mode)
        GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode,
            download_url=self.DOWNLOAD_URL,
            status="downloadable",
            grade=0.98,
        )

    def _check_can_download_certificate(self):
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, u'Download Your ID Verified')
        self.assertContains(response, self.DOWNLOAD_URL)
