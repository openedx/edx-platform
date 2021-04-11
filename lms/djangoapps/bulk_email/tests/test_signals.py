"""
Unit tests for student optouts from course email
"""


import json

from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from mock import Mock, patch
from six import text_type

from lms.djangoapps.bulk_email.models import BulkEmailFlag, Optout
from lms.djangoapps.bulk_email.signals import force_optout_all
from common.djangoapps.student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestOptoutCourseEmailsBySignal(ModuleStoreTestCase):
    """
    Tests that the force_optout_all signal receiver opts the user out of course emails
    """

    def setUp(self):
        super(TestOptoutCourseEmailsBySignal, self).setUp()
        self.course = CourseFactory.create(run='testcourse1', display_name="Test Course Title")
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        self.enrollment = CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.student.username, password="test")

        self.send_mail_url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        self.success_content = {
            'course_id': text_type(self.course.id),
            'success': True,
        }
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    def test_optout_row_created_on_signal(self):
        """
        Make sure the correct row is created for a user enrolled in a course
        """
        force_optout_all(sender=self.__class__, user=self.student)
        self.assertEqual(Optout.objects.filter(user=self.student, course_id=self.course.id).count(), 1)

    def send_test_email(self):
        """
        Navigate to the instructor dash's email view to send bulk email
        """
        # Pull up email view on instructor dashboard
        url = reverse('instructor_dashboard', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.get(url)
        email_section = '<div class="vert-left send-email" id="section-send-email">'

        # If this fails, it is likely because BulkEmailFlag.is_enabled() is set to False
        self.assertContains(response, email_section)

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEqual(json.loads(response.content.decode('utf-8')), self.success_content)

    def test_optout_course(self):
        """
        Make sure student does not receive course email after being opted out
        """
        # Use the signal receiver to for the opt-out
        force_optout_all(sender=self.__class__, user=self.student)

        # Try to send a bulk course email
        self.client.login(username=self.instructor.username, password="test")
        self.send_test_email()

        # Assert that self.student.email not in mail.to, outbox should only contain "myself" target
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEqual(mail.outbox[0].to[0], self.instructor.email)
