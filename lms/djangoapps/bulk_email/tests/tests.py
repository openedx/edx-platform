"""
Unit tests for email feature flag in instructor dashboard
"""

from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestInstructorDashboardEmailView(ModuleStoreTestCase):
    """
    Check for email view displayed with flag
    """
    def setUp(self):
        self.course = CourseFactory.create()

        # Create instructor account
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password="test")

        # URL for instructor dash
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        # URL for email view
        self.email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def test_email_flag_true(self):
        response = self.client.get(self.url)
        self.assertTrue(self.email_link in response.content)

        # Select the Email view of the instructor dash
        session = self.client.session
        session['idash_mode'] = 'Email'
        session.save()
        response = self.client.get(self.url)

        # Ensure we've selected the view properly and that the send_to field is present.
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)
        send_to_label = '<label for="id_to">Send to:</label>'
        self.assertTrue(send_to_label in response.content)

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': False})
    def test_email_flag_false(self):
        response = self.client.get(self.url)
        self.assertFalse(self.email_link in response.content)
