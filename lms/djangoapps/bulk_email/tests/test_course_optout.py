"""
Unit tests for student optouts from course email
"""
import json

from django.core import mail
from django.test.utils import override_settings
from django.core.urlresolvers import reverse
from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestOptoutCourseEmails(ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.instructor = AdminFactory.create()
        self.student = UserFactory.create()
        CourseEnrollmentFactory.create(user=self.student, course_id=self.course.id)

        self.client.login(username=self.student.username, password="test")

    def test_optout_course(self):
        """
        Make sure student does not receive course email after opting out.
        """
        url = reverse('change_email_settings')
        response = self.client.post(url, {'course_id': self.course.id})
        self.assertEquals(json.loads(response.content), {'success': True})

        self.client.logout()
        self.client.login(username=self.instructor.username, password="test")

        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.post(url, {'action': 'Send email', 'to': 'all', 'subject': 'test subject for all', 'message': 'test message for all'})
        self.assertContains(response, "Your email was successfully queued for sending.")

        #assert that self.student.email not in mail.to, outbox should be empty
        self.assertEqual(len(mail.outbox), 0)

    def test_optin_course(self):
        """
        Make sure student receives course email after opting in.
        """
        url = reverse('change_email_settings')
        response = self.client.post(url, {'course_id': self.course.id, 'receive_emails': 'on'})
        self.assertEquals(json.loads(response.content), {'success': True})

        self.client.logout()
        self.client.login(username=self.instructor.username, password="test")

        url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.post(url, {'action': 'Send email', 'to': 'all', 'subject': 'test subject for all', 'message': 'test message for all'})
        self.assertContains(response, "Your email was successfully queued for sending.")

        #assert that self.student.email in mail.to
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.student.email)
