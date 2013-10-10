"""
Unit tests for email feature flag in new instructor dashboard.
Additionally tests that bulk email is always disabled for
non-Mongo backed courses, regardless of email feature flag.
"""

from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestNewInstructorDashboardEmailViewMongoBacked(ModuleStoreTestCase):
    """
    Check for email view on the new instructor dashboard
    for Mongo-backed courses
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard_2', kwargs={'course_id': self.course.id})
        # URL for email view
        self.email_link = '<a href="" data-section="send_email">Email</a>'

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    # In order for bulk email to work, we must have both the ENABLE_INSTRUCTOR_EMAIL_FLAG
    # set to True and for the course to be Mongo-backed.
    # The flag is enabled and the course is Mongo-backed (should work)
    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_email_flag_true_mongo_true(self):
        # Assert that the URL for the email view is in the response
        response = self.client.get(self.url)
        self.assertIn(self.email_link, response.content)

        send_to_label = '<label for="id_to">Send to:</label>'
        self.assertTrue(send_to_label in response.content)
        self.assertEqual(response.status_code, 200)

    # The course is Mongo-backed but the flag is disabled (should not work)
    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false_mongo_true(self):
        # Assert that the URL for the email view is not in the response
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class TestNewInstructorDashboardEmailViewXMLBacked(ModuleStoreTestCase):
    """
    Check for email view on the new instructor dashboard
    """
    def setUp(self):
        self.course_name = 'edX/toy/2012_Fall'

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard_2', kwargs={'course_id': self.course_name})
        # URL for email view
        self.email_link = '<a href="" data-section="send_email">Email</a>'

    # The flag is enabled but the course is not Mongo-backed (should not work)
    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_email_flag_true_mongo_false(self):
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)

    # The flag is disabled and the course is not Mongo-backed (should not work)
    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false_mongo_false(self):
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)
