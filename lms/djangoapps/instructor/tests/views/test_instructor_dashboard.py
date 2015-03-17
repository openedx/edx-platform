"""
Unit tests for instructor_dashboard.py.
"""
from mock import patch

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test.utils import override_settings
from courseware.tests.helpers import LoginEnrollmentTestCase

from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from shoppingcart.models import PaidCourseRegistration
from course_modes.models import CourseMode
from student.roles import CourseFinanceAdminRole


class TestInstructorDashboard(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for the instructor dashboard (not legacy).
    """

    def setUp(self):
        """
        Set up tests
        """
        super(TestInstructorDashboard, self).setUp()
        self.course = CourseFactory.create()

        self.course_mode = CourseMode(course_id=self.course.id,
                                      mode_slug="honor",
                                      mode_display_name="honor cert",
                                      min_price=40)
        self.course_mode.save()
        # Create instructor account
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})

    def tearDown(self):
        """
        Undo patches.
        """
        patch.stopall()

    def get_dashboard_enrollment_message(self):
        """
        Returns expected dashboard enrollment message with link to Insights.
        """
        return 'Enrollment data is now available in <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

    def get_dashboard_demographic_message(self):
        """
        Returns expected dashboard demographic message with link to Insights.
        """
        return 'Demographic data is now available in <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

    def test_default_currency_in_the_html_response(self):
        """
        Test that checks the default currency_symbol ($) in the response
        """
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        response = self.client.get(self.url)
        self.assertTrue('${amount}'.format(amount=total_amount) in response.content)

    @override_settings(PAID_COURSE_REGISTRATION_CURRENCY=['PKR', 'Rs'])
    def test_override_currency_settings_in_the_html_response(self):
        """
        Test that checks the default currency_symbol ($) in the response
        """
        CourseFinanceAdminRole(self.course.id).add_users(self.instructor)
        total_amount = PaidCourseRegistration.get_total_amount_of_purchased_item(self.course.id)
        response = self.client.get(self.url)
        self.assertIn('{currency}{amount}'.format(currency='Rs', amount=total_amount), response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_no_enrollments(self):
        """
        Test enrollment section is hidden.
        """
        response = self.client.get(self.url)
        # no enrollment information should be visible
        self.assertFalse('<h2>Enrollment Information</h2>' in response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': True})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    def test_show_enrollments_data(self):
        """
        Test enrollment data is shown.
        """
        response = self.client.get(self.url)

        # enrollment information visible
        self.assertTrue('<h2>Enrollment Information</h2>' in response.content)
        self.assertTrue('<td>Verified</td>' in response.content)
        self.assertTrue('<td>Audit</td>' in response.content)
        self.assertTrue('<td>Honor</td>' in response.content)

        # dashboard link hidden
        self.assertFalse(self.get_dashboard_enrollment_message() in response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_ENROLLMENTS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_show_dashboard_enrollment_message(self):
        """
        Test enrollment dashboard message is shown and data is hidden.
        """
        response = self.client.get(self.url)

        # enrollment information hidden
        self.assertFalse('<td>Verified</td>' in response.content)
        self.assertFalse('<td>Audit</td>' in response.content)
        self.assertFalse('<td>Honor</td>' in response.content)

        # link to dashboard shown
        expected_message = self.get_dashboard_enrollment_message()
        self.assertTrue(expected_message in response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_DEMOGRAPHICS': True})
    @override_settings(ANALYTICS_DASHBOARD_URL='')
    @override_settings(ANALYTICS_DASHBOARD_NAME='')
    def test_show_dashboard_demographic_data(self):
        """
        Test enrollment demographic data is shown.
        """
        response = self.client.get(self.url)
        # demographic information displayed
        self.assertTrue('data-feature="year_of_birth"' in response.content)
        self.assertTrue('data-feature="gender"' in response.content)
        self.assertTrue('data-feature="level_of_education"' in response.content)

        # dashboard link hidden
        self.assertFalse(self.get_dashboard_demographic_message() in response.content)

    @patch.dict(settings.FEATURES, {'DISPLAY_ANALYTICS_DEMOGRAPHICS': False})
    @override_settings(ANALYTICS_DASHBOARD_URL='http://example.com')
    @override_settings(ANALYTICS_DASHBOARD_NAME='Example')
    def test_show_dashboard_demographic_message(self):
        """
        Test enrollment demographic dashboard message is shown and data is hidden.
        """
        response = self.client.get(self.url)

        # demographics are hidden
        self.assertFalse('data-feature="year_of_birth"' in response.content)
        self.assertFalse('data-feature="gender"' in response.content)
        self.assertFalse('data-feature="level_of_education"' in response.content)

        # link to dashboard shown
        expected_message = self.get_dashboard_demographic_message()
        self.assertTrue(expected_message in response.content)
