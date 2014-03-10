# -*- coding: utf-8 -*-
"""
Unit tests for student optouts from course email
"""
import json

from django.core import mail
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.conf import settings
from django.test.utils import override_settings

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from student.models import CourseEnrollment
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from mock import patch


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestOptoutCourseEmails(ModuleStoreTestCase):

    """
    Test that optouts are referenced in sending course email.
    """

    def setUp(self):
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(display_name=course_title)
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.student.username, password="test")

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    def navigate_to_email_view(self):
        """Navigate to the instructor dash's email view"""
        # Pull up email view on instructor dashboard
        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        response = self.client.get(url)
        email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'
        # If this fails, it is likely because ENABLE_INSTRUCTOR_EMAIL is set to False
        self.assertTrue(email_link in response.content)

        # Select the Email view of the instructor dash
        session = self.client.session
        session['idash_mode'] = 'Email'
        session.save()
        response = self.client.get(url)
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
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

        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(url, test_email)
        self.assertContains(response, "Your email was successfully queued for sending.")

        # Assert that self.student.email not in mail.to, outbox should be empty
        self.assertEqual(len(mail.outbox), 0)

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
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

        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        # Assert that self.student.email in mail.to
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.student.email)
