# -*- coding: utf-8 -*-
"""
Unit tests for student optouts from course email
"""


import json

from django.core import mail
from django.core.management import call_command
from django.urls import reverse
from edx_ace.channel import ChannelType
from edx_ace.message import Message
from edx_ace.policy import PolicyResult
from edx_ace.recipient import Recipient
from mock import Mock, patch
from six import text_type

from lms.djangoapps.bulk_email.models import BulkEmailFlag
from lms.djangoapps.bulk_email.policies import CourseEmailOptout
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import AdminFactory, CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from lms.djangoapps.bulk_email.api import get_unsubscribed_link


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestOptoutCourseEmails(ModuleStoreTestCase):
    """
    Test that optouts are referenced in sending course email.
    """

    def setUp(self):
        super(TestOptoutCourseEmails, self).setUp()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(run='testcourse1', display_name=course_title)
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.student.username, password="test")

        self.send_mail_url = reverse('send_email', kwargs={'course_id': text_type(self.course.id)})
        self.success_content = {
            'course_id': text_type(self.course.id),
            'success': True,
        }
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    def navigate_to_email_view(self):
        """Navigate to the instructor dash's email view"""
        # Pull up email view on instructor dashboard
        url = reverse('instructor_dashboard', kwargs={'course_id': text_type(self.course.id)})
        response = self.client.get(url)
        email_section = '<div class="vert-left send-email" id="section-send-email">'
        # If this fails, it is likely because BulkEmailFlag.is_enabled() is set to False
        self.assertContains(response, email_section)

    def test_optout_course(self):
        """
        Make sure student does not receive course email after opting out.
        """
        url = reverse('change_email_settings')
        # This is a checkbox, so on the post of opting out (that is, an Un-check of the box),
        # the Post that is sent will not contain 'receive_emails'
        response = self.client.post(url, {'course_id': text_type(self.course.id)})
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

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
        self.assertEqual(json.loads(response.content.decode('utf-8')), self.success_content)

        # Assert that self.student.email not in mail.to, outbox should only contain "myself" target
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to[0], self.instructor.email)

    def test_optout_using_unsubscribe_link_in_email(self):
        """
        Make sure email is't sent to learner after opt out.
        """
        self.client.logout()

        self.client.login(username=self.instructor.username, password="test")

        unsubscribe_link = get_unsubscribed_link(self.student.username, text_type(self.course.id))
        response = self.client.post(unsubscribe_link, {'unsubscribe': True})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'You have successfully unsubscribed from')

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "learners"]',
            'subject': 'Checking unsubscribe link in email',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEqual(json.loads(response.content.decode('utf-8')), self.success_content)
        self.assertEqual(len(mail.outbox), 1)

    def test_optin_course(self):
        """
        Make sure student receives course email after opting in.
        """
        url = reverse('change_email_settings')
        response = self.client.post(url, {'course_id': text_type(self.course.id), 'receive_emails': 'on'})
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

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
        self.assertEqual(json.loads(response.content.decode('utf-8')), self.success_content)

        # Assert that self.student.email in mail.to, along with "myself" target
        self.assertEqual(len(mail.outbox), 2)
        sent_addresses = [message.to[0] for message in mail.outbox]
        self.assertIn(self.student.email, sent_addresses)
        self.assertIn(self.instructor.email, sent_addresses)


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestACEOptoutCourseEmails(ModuleStoreTestCase):
    """
    Test that optouts are referenced in sending course email.
    """

    def setUp(self):
        super(TestACEOptoutCourseEmails, self).setUp()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(run='testcourse1', display_name=course_title)
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        self.client.login(username=self.student.username, password="test")

        self._set_email_optout(False)
        self.policy = CourseEmailOptout()

    def _set_email_optout(self, opted_out):
        url = reverse('change_email_settings')
        # This is a checkbox, so on the post of opting out (that is, an Un-check of the box),
        # the Post that is sent will not contain 'receive_emails'
        post_data = {'course_id': text_type(self.course.id)}

        if not opted_out:
            post_data['receive_emails'] = 'on'

        response = self.client.post(url, post_data)
        self.assertEqual(json.loads(response.content.decode('utf-8')), {'success': True})

    def test_policy_optedout(self):
        """
        Make sure the policy prevents ACE emails if the user is opted-out.
        """
        self._set_email_optout(True)

        channel_mods = self.policy.check(self.create_test_message())
        self.assertEqual(channel_mods, PolicyResult(deny={ChannelType.EMAIL}))

    def create_test_message(self):
        return Message(
            app_label='foo',
            name='bar',
            recipient=Recipient(
                username=self.student.username,
                email_address=self.student.email,
            ),
            context={
                'course_ids': [str(self.course.id)]
            },
        )

    def test_policy_optedin(self):
        """
        Make sure the policy allows ACE emails if the user is opted-in.
        """
        channel_mods = self.policy.check(self.create_test_message())
        self.assertEqual(channel_mods, PolicyResult(deny=set()))

    def test_policy_no_course_id(self):
        """
        Make sure the policy denies ACE emails if there is no course id in the context.
        """
        message = self.create_test_message()
        message.context = {}
        channel_mods = self.policy.check(message)
        self.assertEqual(channel_mods, PolicyResult(deny=set()))
