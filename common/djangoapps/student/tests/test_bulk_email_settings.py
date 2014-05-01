"""
Unit tests for email feature flag in student dashboard. Additionally tests
that bulk email is always disabled for non-Mongo backed courses, regardless
of email feature flag, and that the view is conditionally available when
Course Auth is turned on.
"""

from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from unittest.case import SkipTest

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.locations import SlashSeparatedCourseKey

from bulk_email.models import CourseAuthorization

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestStudentDashboardEmailView(ModuleStoreTestCase):
    """
    Check for email view displayed with flag
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create student account
        student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        self.client.login(username=student.username, password="test")

        try:
            # URL for dashboard
            self.url = reverse('dashboard')
        except NoReverseMatch:
            raise SkipTest("Skip this test if url cannot be found (ie running from CMS tests)")
        # URL for email settings modal
        self.email_modal_link = (
            ('<a href="#email-settings-modal" class="email-settings" rel="leanModal" '
             'data-course-id="{0}/{1}/{2}" data-course-number="{1}" '
             'data-optout="False">Email Settings</a>').format(
                 self.course.org,
                 self.course.number,
                 self.course.display_name.replace(' ', '_')
             )
        )

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_true(self):
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertTrue(self.email_modal_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false(self):
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_unauthorized(self):
        # Assert that instructor email is not enabled for this course
        self.assertFalse(CourseAuthorization.instructor_email_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        # if this course isn't authorized
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_authorized(self):
        # Authorize the course to use email
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()
        # Assert that instructor email is enabled for this course
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))
        # Assert that the URL for the email view is not in the response
        # if this course isn't authorized
        response = self.client.get(self.url)
        self.assertTrue(self.email_modal_link in response.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestStudentDashboardEmailViewXMLBacked(ModuleStoreTestCase):
    """
    Check for email view on student dashboard, with XML backed course.
    """
    def setUp(self):
        self.course_name = 'edX/toy/2012_Fall'

        # Create student account
        student = UserFactory.create()
        CourseEnrollmentFactory.create(
            user=student,
            course_id=SlashSeparatedCourseKey.from_deprecated_string(self.course_name)
        )
        self.client.login(username=student.username, password="test")

        try:
            # URL for dashboard
            self.url = reverse('dashboard')
        except NoReverseMatch:
            raise SkipTest("Skip this test if url cannot be found (ie running from CMS tests)")

        # URL for email settings modal
        self.email_modal_link = (
            ('<a href="#email-settings-modal" class="email-settings" rel="leanModal" '
             'data-course-id="{0}/{1}/{2}" data-course-number="{1}" '
             'data-optout="False">Email Settings</a>').format(
                 'edX',
                 'toy',
                 '2012_Fall'
             )
        )

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_true_xml_store(self):
        # The flag is enabled, and since REQUIRE_COURSE_EMAIL_AUTH is False, all courses should
        # be authorized to use email. But the course is not Mongo-backed (should not work)
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_false_xml_store(self):
        # Email disabled, shouldn't see link.
        response = self.client.get(self.url)
        self.assertFalse(self.email_modal_link in response.content)
