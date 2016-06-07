"""
Unit tests for email feature flag in student dashboard. Additionally tests
that bulk email is always disabled for non-Mongo backed courses, regardless
of email feature flag, and that the view is conditionally available when
Course Auth is turned on.
"""
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory

# This import is for an lms djangoapp.
# Its testcases are only run under lms.
from bulk_email.models import CourseAuthorization, BulkEmailFlag  # pylint: disable=import-error


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardEmailView(SharedModuleStoreTestCase):
    """
    Check for email view displayed with flag
    """
    @classmethod
    def setUpClass(cls):
        super(TestStudentDashboardEmailView, cls).setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super(TestStudentDashboardEmailView, self).setUp()

        # Create student account
        student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        self.client.login(username=student.username, password="test")

        self.url = reverse('dashboard')
        # URL for email settings modal
        self.email_modal_link = (
            '<a href="#email-settings-modal" class="action action-email-settings" rel="leanModal" '
            'data-course-id="{org}/{num}/{name}" data-course-number="{num}" '
            'data-dashboard-index="0" data-optout="False">Email Settings</a>'
        ).format(
            org=self.course.org,
            num=self.course.number,
            name=self.course.display_name.replace(' ', '_'),
        )

    def tearDown(self):
        super(TestStudentDashboardEmailView, self).tearDown()
        BulkEmailFlag.objects.all().delete()

    def test_email_flag_true(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertTrue(self.email_modal_link in response.content)

    def test_email_flag_false(self):
        BulkEmailFlag.objects.create(enabled=False)
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertNotIn(self.email_modal_link, response.content)

    def test_email_unauthorized(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        # Assert that instructor email is not enabled for this course
        self.assertFalse(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        # if this course isn't authorized
        response = self.client.get(self.url)
        self.assertNotIn(self.email_modal_link, response.content)

    def test_email_authorized(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=True)
        # Authorize the course to use email
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()
        # Assert that instructor email is enabled for this course
        self.assertTrue(BulkEmailFlag.feature_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        # if this course isn't authorized
        response = self.client.get(self.url)
        self.assertTrue(self.email_modal_link in response.content)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardEmailViewXMLBacked(SharedModuleStoreTestCase):
    """
    Check for email view on student dashboard, with XML backed course.
    """
    MODULESTORE = TEST_DATA_MIXED_MODULESTORE

    def setUp(self):
        super(TestStudentDashboardEmailViewXMLBacked, self).setUp()
        self.course_name = 'edX/toy/2012_Fall'

        # Create student account
        student = UserFactory.create()
        CourseEnrollmentFactory.create(
            user=student,
            course_id=SlashSeparatedCourseKey.from_deprecated_string(self.course_name)
        )
        self.client.login(username=student.username, password="test")

        self.url = reverse('dashboard')

        # URL for email settings modal
        self.email_modal_link = (
            '<a href="#email-settings-modal" class="action action-email-settings" rel="leanModal" '
            'data-course-id="{org}/{num}/{name}" data-course-number="{num}" '
            'data-dashboard-index="0" data-optout="False">Email Settings</a>'
        ).format(
            org='edX',
            num='toy',
            name='2012_Fall',
        )

    def test_email_flag_true_xml_store(self):
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)
        # The flag is enabled, and since REQUIRE_COURSE_EMAIL_AUTH is False, all courses should
        # be authorized to use email. But the course is not Mongo-backed (should not work)
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)

    def test_email_flag_false_xml_store(self):
        BulkEmailFlag.objects.create(enabled=False, require_course_email_auth=False)
        # Email disabled, shouldn't see link.
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)
