"""Tests for display of certificates on the student dashboard. """

import unittest
import ddt

from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error
from certificates.api import get_certificate_url  # pylint: disable=import-error

# pylint: disable=no-member


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
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_display_verified_certificate(self, enrollment_mode):
        self._create_certificate(enrollment_mode)
        self._check_can_download_certificate()

    @ddt.data('verified', 'honor')
    @override_settings(CERT_NAME_SHORT='Test_Certificate')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_display_download_certificate_button(self, enrollment_mode):
        """
        Tests if CERTIFICATES_HTML_VIEW is True and there is no active certificate configuration available
        then any of the Download certificate button should not be visible.
        """
        self._create_certificate(enrollment_mode)
        self._check_can_not_download_certificate()

    @ddt.data('verified')
    @override_settings(CERT_NAME_SHORT='Test_Certificate')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_linked_student_to_web_view_credential(self, enrollment_mode):
        test_url = get_certificate_url(
            user_id=self.user.id,
            course_id=unicode(self.course.id),
            verify_uuid='abcdefg12345678'
        )

        self._create_certificate(enrollment_mode)
        certificates = [
            {
                'id': 0,
                'name': 'Test Name',
                'description': 'Test Description',
                'is_active': True,
                'signatories': [],
                'version': 1
            }
        ]
        self.course.certificates = {'certificates': certificates}
        self.course.save()   # pylint: disable=no-member
        self.store.update_item(self.course, self.user.id)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, u'View Test_Certificate')
        self.assertContains(response, test_url)

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

    def _check_can_not_download_certificate(self):
        """
        Make sure response does not have any of the download certificate buttons
        """
        response = self.client.get(reverse('dashboard'))
        self.assertNotContains(response, u'View Test_Certificate')
        self.assertNotContains(response, u'Download Your Test_Certificate (PDF)')
        self.assertNotContains(response, u'Download Test_Certificate (PDF)')
        self.assertNotContains(response, self.DOWNLOAD_URL)
