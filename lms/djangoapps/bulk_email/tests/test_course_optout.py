# -*- coding: utf-8 -*-
"""
Unit tests for student optouts from course email
"""
import json
from mock import patch, Mock
from nose.plugins.attrib import attr

from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings

from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from bulk_email.models import BulkEmailFlag


@attr('shard_1')
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestOptoutCourseEmails(ModuleStoreTestCase):
    """
    Test that optouts are referenced in sending course email.
    """

    def setUp(self):
        super(TestOptoutCourseEmails, self).setUp()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(display_name=course_title)
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.student.username, password="test")

        self.send_mail_url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.success_content = {
            'course_id': self.course.id.to_deprecated_string(),
            'success': True,
        }
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    def tearDown(self):
        super(TestOptoutCourseEmails, self).tearDown()
        BulkEmailFlag.objects.all().delete()

    def navigate_to_email_view(self):
        """Navigate to the instructor dash's email view"""
        # Pull up email view on instructor dashboard
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        email_section = '<div class="vert-left send-email" id="section-send-email">'
        # If this fails, it is likely because BulkEmailFlag.is_enabled() is set to False
        self.assertTrue(email_section in response.content)

    def test_optout_course(self):
        """
        Make sure student does not receive course email after opting out.
        """
        url = reverse('change_email_settings')
        # This is a checkbox, so on the post of opting out (that is, an Un-check of the box),
        # the Post that is sent will not contain 'receive_emails'
        response = self.client.post(url, {'course_id': self.course.id.to_deprecated_string()})
        self.assertEquals(json.loads(response.content), {'success': True})

        self.client.logout()

        self.client.login(username=self.instructor.username, password="test")
        self.navigate_to_email_view()

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # Assert that self.student.email not in mail.to, outbox should only contain "myself" target
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.instructor.email)

    def test_optin_course(self):
        """
        Make sure student receives course email after opting in.
        """
        url = reverse('change_email_settings')
        response = self.client.post(url, {'course_id': self.course.id.to_deprecated_string(), 'receive_emails': 'on'})
        self.assertEquals(json.loads(response.content), {'success': True})

        self.client.logout()

        self.assertTrue(CourseEnrollment.is_enrolled(self.student, self.course.id))

        self.client.login(username=self.instructor.username, password="test")
        self.navigate_to_email_view()

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # Assert that self.student.email in mail.to, along with "myself" target
        self.assertEqual(len(mail.outbox), 2)
        sent_addresses = [message.to[0] for message in mail.outbox]
        self.assertIn(self.student.email, sent_addresses)
        self.assertIn(self.instructor.email, sent_addresses)
