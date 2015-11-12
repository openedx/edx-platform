"""
Unit tests for email feature flag in student dashboard. Additionally tests
that bulk email is always disabled for non-Mongo backed courses, regardless
of email feature flag, and that the view is conditionally available when
Course Auth is turned on.
"""
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse
from mock import patch
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from student.tests.factories import UserFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.django_utils import TEST_DATA_MIXED_TOY_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory

# This import is for an lms djangoapp.
# Its testcases are only run under lms.
from bulk_email.models import CourseAuthorization  # pylint: disable=import-error


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardEmailView(ModuleStoreTestCase):
    """
    Check for email view displayed with flag
    """

    def setUp(self):
        super(TestStudentDashboardEmailView, self).setUp()

        self.course = CourseFactory.create()

        # Create student account
        student = UserFactory.create()
        CourseEnrollmentFactory.create(user=student, course_id=self.course.id)
        self.client.login(username=student.username, password="test")

        self.url = reverse('dashboard')

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_true(self):
        """
        Assert that the email settings link can be visible.
        """
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": true', 1)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false(self):
        """
        Assert that the email settings link can't be visible.
        """
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": false', 1)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_unauthorized(self):
        """
        Assert that instructor email is not enabled for this course and
        the email settings link can't be visible if this course isn't
        authorized.
        """
        self.assertFalse(CourseAuthorization.instructor_email_enabled(self.course.id))
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": false', 1)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_authorized(self):
        """
        Assert that instructor email is enabled for this course and
        the email settings link can be visible if this course is
        authorized.
        """
        cauth = CourseAuthorization(course_id=self.course.id, email_enabled=True)
        cauth.save()
        self.assertTrue(CourseAuthorization.instructor_email_enabled(self.course.id))
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": true', 1)


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class TestStudentDashboardEmailViewXMLBacked(ModuleStoreTestCase):
    """
    Check for email view on student dashboard, with XML backed course.
    """
    MODULESTORE = TEST_DATA_MIXED_TOY_MODULESTORE

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

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_true_xml_store(self):
        """
        The flag is enabled, and since REQUIRE_COURSE_EMAIL_AUTH is False,
        all courses should be authorized to use email. But the course is
        not Mongo-backed and the email settings link can't be visible.
        """
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": false', 1)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def test_email_flag_false_xml_store(self):
        """
        Assert that instructor email is not enabled for this course and
        the email settings link can't be visible.
        """
        response = self.client.get(self.url)
        self.assertContains(response, '"show_email_settings": false', 1)
