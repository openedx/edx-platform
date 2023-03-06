"""Tests for display of certificates on the student dashboard. """

import datetime
from unittest.mock import patch

import ddt
from django.conf import settings
from django.test.utils import override_settings
from django.urls import reverse
from pytz import UTC
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.django_utils import TEST_DATA_MONGO_AMNESTY_MODULESTORE, SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.data import CertificatesDisplayBehaviors

from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory
from openedx.core.djangolib.testing.utils import skip_unless_lms
from lms.djangoapps.certificates.api import get_certificate_url
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.tests.factories import (
    GeneratedCertificateFactory,
    LinkedInAddToProfileConfigurationFactory
)

# pylint: disable=no-member

PAST_DATE = datetime.datetime.now(UTC) - datetime.timedelta(days=2)
FUTURE_DATE = datetime.datetime.now(UTC) + datetime.timedelta(days=2)


class CertificateDisplayTestBase(SharedModuleStoreTestCase):
    """Tests display of certificates on the student dashboard. """

    MODULESTORE = TEST_DATA_MONGO_AMNESTY_MODULESTORE
    USERNAME = "test_user"
    PASSWORD = "password"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory()
        cls.course.certificates_display_behavior = CertificatesDisplayBehaviors.EARLY_NO_INFO

        with cls.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, cls.course.id):
            cls.store.update_item(cls.course, cls.USERNAME)

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create(username=self.USERNAME, password=self.PASSWORD)
        result = self.client.login(username=self.USERNAME, password=self.PASSWORD)
        assert result, 'Could not log in'

    def _check_linkedin_visibility(self, is_visible):
        """
        Performs assertions on the Dashboard
        """
        response = self.client.get(reverse('dashboard'))
        if is_visible:
            self.assertContains(response, 'Add Certificate to LinkedIn Profile')
        else:
            self.assertNotContains(response, 'Add Certificate to LinkedIn Profile')

    def _create_certificate(self, enrollment_mode):
        """Simulate that the user has a generated certificate. """
        CourseEnrollmentFactory.create(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode)
        return GeneratedCertificateFactory(
            user=self.user,
            course_id=self.course.id,
            mode=enrollment_mode,
            status=CertificateStatuses.downloadable,
            grade=0.98,
        )


@ddt.ddt
@skip_unless_lms
class CertificateDashboardMessageDisplayTest(CertificateDisplayTestBase):
    """
    Tests the certificates messages for a course in the dashboard.
    """

    ENABLED_SIGNALS = ['course_published']

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course.certificates_display_behavior = CertificatesDisplayBehaviors.END_WITH_DATE
        cls.course.save()
        cls.store.update_item(cls.course, cls.USERNAME)

    def _check_message(self, visible_date):  # lint-amnesty, pylint: disable=missing-function-docstring
        response = self.client.get(reverse('dashboard'))
        test_message = 'Your grade and certificate will be ready after'

        is_past = visible_date < datetime.datetime.now(UTC)

        if is_past:
            self.assertNotContains(response, test_message)
            self.assertNotContains(response, "View Test_Certificate")

        else:
            self.assertContains(response, test_message)
            self.assertNotContains(response, "View Test_Certificate")

    @ddt.data(
        (CertificatesDisplayBehaviors.END, True),
        (CertificatesDisplayBehaviors.END, False),
        (CertificatesDisplayBehaviors.END_WITH_DATE, True),
        (CertificatesDisplayBehaviors.END_WITH_DATE, False)
    )
    @ddt.unpack
    def test_certificate_available_date(self, certificates_display_behavior, past_date):
        cert = self._create_certificate('verified')
        cert.status = CertificateStatuses.downloadable
        cert.save()

        self.course.certificates_display_behavior = certificates_display_behavior

        if certificates_display_behavior == CertificatesDisplayBehaviors.END:
            if past_date:
                self.course.end = PAST_DATE
            else:
                self.course.end = FUTURE_DATE
        if certificates_display_behavior == CertificatesDisplayBehaviors.END_WITH_DATE:
            if past_date:
                self.course.certificate_available_date = PAST_DATE
            else:
                self.course.certificate_available_date = FUTURE_DATE

        self.course.save()
        self.store.update_item(self.course, self.USERNAME)

        self._check_message(PAST_DATE if past_date else FUTURE_DATE)


@ddt.ddt
@skip_unless_lms
class CertificateDisplayTest(CertificateDisplayTestBase):
    """
    Tests of certificate display.
    """

    @ddt.data('verified', 'honor', 'professional')
    def test_unverified_certificate_message(self, enrollment_mode):
        cert = self._create_certificate(enrollment_mode)
        cert.status = CertificateStatuses.unverified
        cert.save()
        response = self.client.get(reverse('dashboard'))
        self.assertContains(
            response,
            'do not have a current verified identity with {platform_name}'
            .format(platform_name=settings.PLATFORM_NAME))

    def test_post_to_linkedin_visibility(self):
        """
        Verifies that the post certificate to linked button
        does not appear by default (when config is not set)
        Then Verifies that the post certificate to linked button appears
        as expected once a config is set
        """
        self._create_certificate('honor')

        # until we set up the configuration, the LinkedIn action
        # button should not be visible
        self._check_linkedin_visibility(False)

        LinkedInAddToProfileConfigurationFactory()
        # now we should see it
        self._check_linkedin_visibility(True)


@ddt.ddt
@skip_unless_lms
class CertificateDisplayTestLinkedHtmlView(CertificateDisplayTestBase):
    """
    Tests of linked student certificates.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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

        self.assertContains(response, 'View my Test_Certificate')
        self.assertContains(response, test_url)
