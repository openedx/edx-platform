"""Tests for display of certificates on the student dashboard. """

import unittest
import ddt
import mock

from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from django.test.utils import override_settings
from xmodule.modulestore import ModuleStoreEnum

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from certificates.tests.factories import GeneratedCertificateFactory  # pylint: disable=import-error
from certificates.api import get_certificate_url  # pylint: disable=import-error
from certificates.models import CertificateStatuses  # pylint: disable=import-error
from course_modes.models import CourseMode

from student.models import LinkedInAddToProfileConfiguration

# pylint: disable=no-member


class CertificateDisplayTestBase(SharedModuleStoreTestCase):
    """Tests display of certificates on the student dashboard. """

    USERNAME = "test_user"
    PASSWORD = "password"
    DOWNLOAD_URL = "http://www.example.com/certificate.pdf"

    @classmethod
    def setUpClass(cls):
        super(CertificateDisplayTestBase, cls).setUpClass()
        cls.course = CourseFactory()
        cls.course.certificates_display_behavior = "early_with_info"

        with cls.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, cls.course.id):
            cls.store.update_item(cls.course, cls.USERNAME)

    def setUp(self):
        super(CertificateDisplayTestBase, self).setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        self.assertTrue(result, msg="Could not log in")

    def _check_linkedin_visibility(self, is_visible):
        """
        Performs assertions on the Dashboard
        """
        response = self.client.get(reverse('dashboard'))
        if is_visible:
            self.assertContains(response, u'Add Certificate to LinkedIn Profile')
        else:
            self.assertNotContains(response, u'Add Certificate to LinkedIn Profile')

    def _create_certificate(self, enrollment_mode):
        """Simulate that the user has a generated certificate. """
        CourseEnrollmentFactory.create(user=self.user, course_id=self.course.id, mode=enrollment_mode)
        return GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode,
            download_url=self.DOWNLOAD_URL,
            status="downloadable",
            grade=0.98,
        )

    def _check_can_download_certificate(self):
        """
        Inspect the dashboard to see if a certificate can be downloaded.
        """
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, u'Download Your ID Verified')
        self.assertContains(response, self.DOWNLOAD_URL)

    def _check_can_download_certificate_no_id(self):
        """
        Inspects the dashboard to see if a certificate for a non verified course enrollment
        is present
        """
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, u'Download')
        self.assertContains(response, u'(PDF)')
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


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CertificateDisplayTest(CertificateDisplayTestBase):
    """
    Tests of certificate display.
    """

    @ddt.data('verified', 'professional')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_display_verified_certificate(self, enrollment_mode):
        self._create_certificate(enrollment_mode)
        self._check_can_download_certificate()

    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': False})
    def test_display_verified_certificate_no_id(self):
        """
        Confirm that if we get a certificate with a no-id-professional mode
        we still can download our certificate
        """
        self._create_certificate(CourseMode.NO_ID_PROFESSIONAL_MODE)
        self._check_can_download_certificate_no_id()

    @ddt.data('verified', 'honor', 'professional')
    def test_unverified_certificate_message(self, enrollment_mode):
        cert = self._create_certificate(enrollment_mode)
        cert.status = CertificateStatuses.unverified
        cert.save()
        response = self.client.get(reverse('dashboard'))
        self.assertContains(
            response,
            u'do not have a current verified identity with {platform_name}'
            .format(platform_name=settings.PLATFORM_NAME))

    def test_post_to_linkedin_invisibility(self):
        """
        Verifies that the post certificate to linked button
        does not appear by default (when config is not set)
        """
        self._create_certificate('honor')

        # until we set up the configuration, the LinkedIn action
        # button should not be visible
        self._check_linkedin_visibility(False)

    def test_post_to_linkedin_visibility(self):
        """
        Verifies that the post certificate to linked button appears
        as expected
        """
        self._create_certificate('honor')

        config = LinkedInAddToProfileConfiguration(
            company_identifier='0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9',
            enabled=True
        )
        config.save()

        # now we should see it
        self._check_linkedin_visibility(True)

    @mock.patch("openedx.core.djangoapps.theming.helpers.is_request_in_themed_site", mock.Mock(return_value=True))
    def test_post_to_linkedin_site_specific(self):
        """
        Verifies behavior for themed sites which disables the post to LinkedIn
        feature (for now)
        """
        self._create_certificate('honor')

        config = LinkedInAddToProfileConfiguration(
            company_identifier='0_mC_o2MizqdtZEmkVXjH4eYwMj4DnkCWrZP_D9',
            enabled=True
        )
        config.save()

        # now we should not see it because we are in a themed site
        self._check_linkedin_visibility(False)


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CertificateDisplayTestHtmlView(CertificateDisplayTestBase):
    """
    Tests of webview certificate display
    """

    @classmethod
    def setUpClass(cls):
        super(CertificateDisplayTestHtmlView, cls).setUpClass()
        cls.course.cert_html_view_enabled = True
        cls.course.save()
        cls.store.update_item(cls.course, cls.USERNAME)

    @ddt.data('verified', 'honor')
    @override_settings(CERT_NAME_SHORT='Test_Certificate')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_display_download_certificate_button(self, enrollment_mode):
        """
        Tests if CERTIFICATES_HTML_VIEW is True
        and course has enabled web certificates via cert_html_view_enabled setting
        and no active certificate configuration available
        then any of the Download certificate button should not be visible.
        """
        self._create_certificate(enrollment_mode)
        self._check_can_not_download_certificate()


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class CertificateDisplayTestLinkedHtmlView(CertificateDisplayTestBase):
    """
    Tests of linked student certificates.
    """

    @classmethod
    def setUpClass(cls):
        super(CertificateDisplayTestLinkedHtmlView, cls).setUpClass()
        cls.course.cert_html_view_enabled = True

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
        cls.course.certificates = {'certificates': certificates}

        cls.course.save()
        cls.store.update_item(cls.course, cls.USERNAME)

    @ddt.data('verified')
    @override_settings(CERT_NAME_SHORT='Test_Certificate')
    @patch.dict('django.conf.settings.FEATURES', {'CERTIFICATES_HTML_VIEW': True})
    def test_linked_student_to_web_view_credential(self, enrollment_mode):

        cert = self._create_certificate(enrollment_mode)
        test_url = get_certificate_url(course_id=self.course.id, uuid=cert.verify_uuid)

        response = self.client.get(reverse('dashboard'))

        self.assertContains(response, u'View Test_Certificate')
        self.assertContains(response, test_url)
