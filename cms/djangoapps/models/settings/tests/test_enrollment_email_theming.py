"""
Test that theming works (for enrollment email template).
"""
from django.test import TestCase
from django.test.utils import override_settings

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from models.settings.course_details import CourseDetails


class EnrollmentEmailThemingTestCase(TestCase):
    """
    Tests that theming for enrollment email works.
    """
    @override_settings(DEFAULT_PRE_ENROLLMENT_EMAIL='This is a test pre enrollment email template.')
    def test_pre_enrollment_email_theming(self):
        """
        Test that settings override template is used for default email on enrolling before course start.
        """
        course_key = SlashSeparatedCourseKey('mitX', '101', 'test')
        template = CourseDetails.get_default_pre_enrollment_email(course_key)
        self.assertIn(u'This is a test pre enrollment email template.', template)

    @override_settings(DEFAULT_POST_ENROLLMENT_EMAIL='This is a test post enrollment email template.')
    def test_post_enrollment_email_theming(self):
        """
        Test that settings override template is used for default email on enrolling after course start.
        """
        template = CourseDetails.get_default_post_enrollment_email()
        self.assertIn(u'This is a test post enrollment email template.', template)
