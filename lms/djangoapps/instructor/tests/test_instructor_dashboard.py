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


class TestInstructorDashboard(ModuleStoreTestCase, LoginEnrollmentTestCase):
    """
    Tests for the instructor dashboard (not legacy).
    """

    def setUp(self):
        """
        Set up tests
        """
        self.course = CourseFactory.create()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})

    def tearDown(self):
        """
        Undo patches.
        """
        patch.stopall()

    def get_dashboard_enrollment_message(self):
        return 'Enrollment data is now available in <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

    def get_dashboard_demographic_message(self):
        return 'Demographic data is now available in <a href="http://example.com/courses/{}" ' \
               'target="_blank">Example</a>.'.format(unicode(self.course.id))

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
