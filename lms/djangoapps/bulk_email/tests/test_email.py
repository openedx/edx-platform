# -*- coding: utf-8 -*-
"""
Unit tests for sending course email
"""
from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test.utils import override_settings

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from student.tests.factories import UserFactory, GroupFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from instructor_task.models import InstructorTask
from instructor_task.tests.factories import InstructorTaskFactory

from bulk_email.tasks import send_course_email
from bulk_email.models import CourseEmail, Optout

from mock import patch

STAFF_COUNT = 3
STUDENT_COUNT = 10
LARGE_NUM_EMAILS = 137


class MockCourseEmailResult(object):
    """
    A small closure-like class to keep count of emails sent over all tasks, recorded
    by mock object side effects
    """
    emails_sent = 0

    def get_mock_course_email_result(self):
        """Wrapper for mock email function."""
        def mock_course_email_result(prev_results, sent, failed, output, **kwargs):  # pylint: disable=W0613
            """Increments count of number of emails sent."""
            self.emails_sent += sent
            return True
        return mock_course_email_result


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmailSendFromDashboard(ModuleStoreTestCase):
    """
    Test that emails send correctly.
    """

    @patch.dict(settings.MITX_FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True})
    def setUp(self):
        self.course = CourseFactory.create()
        self.instructor = UserFactory.create(username="instructor", email="robot+instructor@edx.org")
        # Create instructor group for course
        instructor_group = GroupFactory.create(name="instructor_MITx/999/Robot_Super_Course")
        instructor_group.user_set.add(self.instructor)

        # Create staff
        self.staff = [UserFactory() for _ in xrange(STAFF_COUNT)]
        staff_group = GroupFactory()
        for staff in self.staff:
            staff_group.user_set.add(staff)  # pylint: disable=E1101

        # Create students
        self.students = [UserFactory() for _ in xrange(STUDENT_COUNT)]
        for student in self.students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.instructor.username, password="test")

        # Pull up email view on instructor dashboard
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})
        response = self.client.get(self.url)
        email_link = '<a href="#" onclick="goto(\'Email\')" class="None">Email</a>'
        # If this fails, it is likely because ENABLE_INSTRUCTOR_EMAIL is set to False
        self.assertTrue(email_link in response.content)

        # Select the Email view of the instructor dash
        session = self.client.session
        session['idash_mode'] = 'Email'
        session.save()
        response = self.client.get(self.url)
        selected_email_link = '<a href="#" onclick="goto(\'Email\')" class="selectedmode">Email</a>'
        self.assertTrue(selected_email_link in response.content)

    def tearDown(self):
        """
        Undo all patches.
        """
        patch.stopall()

    def test_send_to_self(self):
        """
        Make sure email send to myself goes to myself.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.instructor.email)
        self.assertEquals(
            mail.outbox[0].subject,
            '[' + self.course.display_name + ']' + ' test subject for myself'
        )

    def test_send_to_staff(self):
        """
        Make sure email send to staff and instructors goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'Send email',
            'to_option': 'staff',
            'subject': 'test subject for staff',
            'message': 'test message for subject'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        # the 1 is for the instructor in this test and others
        self.assertEquals(len(mail.outbox), 1 + len(self.staff))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff]
        )

    def test_send_to_all(self):
        """
        Make sure email send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    def test_unicode_subject_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        uni_subject = u'téśt śúbjéćt főŕ áĺĺ'
        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': uni_subject,
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )
        self.assertEquals(
            mail.outbox[0].subject,
            '[' + self.course.display_name + '] ' + uni_subject
        )

    def test_unicode_message_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        uni_message = u'ẗëṡẗ ṁëṡṡäġë ḟöṛ äḷḷ ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ fоѓ аll'
        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': uni_message
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

        message_body = mail.outbox[0].body
        self.assertIn(uni_message, message_body)

    def test_unicode_students_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        # Create a student with Unicode in their first & last names
        unicode_user = UserFactory(first_name=u'Ⓡⓞⓑⓞⓣ', last_name=u'ՇﻉรՇ')
        CourseEnrollmentFactory.create(user=unicode_user, course_id=self.course.id)
        self.students.append(unicode_user)

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)

        self.assertContains(response, "Your email was successfully queued for sending.")

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))

        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    @override_settings(EMAILS_PER_TASK=3, EMAILS_PER_QUERY=7)
    @patch('bulk_email.tasks._course_email_result')
    def test_chunked_queries_send_numerous_emails(self, email_mock):
        """
        Test sending a large number of emails, to test the chunked querying
        """
        mock_factory = MockCourseEmailResult()
        email_mock.side_effect = mock_factory.get_mock_course_email_result()
        added_users = []
        for _ in xrange(LARGE_NUM_EMAILS):
            user = UserFactory()
            added_users.append(user)
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        optouts = []
        for i in [1, 3, 9, 10, 18]:  # 5 random optouts
            user = added_users[i]
            optouts.append(user)
            optout = Optout(user=user, course_id=self.course.id)
            optout.save()

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.url, test_email)
        self.assertContains(response, "Your email was successfully queued for sending.")
        self.assertEquals(mock_factory.emails_sent,
                          1 + len(self.staff) + len(self.students) + LARGE_NUM_EMAILS - len(optouts))
        outbox_contents = [e.to[0] for e in mail.outbox]
        should_send_contents = ([self.instructor.email] +
                                [s.email for s in self.staff] +
                                [s.email for s in self.students] +
                                [s.email for s in added_users if s not in optouts])
        self.assertItemsEqual(outbox_contents, should_send_contents)


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmailSendExceptions(ModuleStoreTestCase):
    """
    Test that exceptions are handled correctly.
    """
    def test_no_instructor_task(self):
        with self.assertRaises(InstructorTask.DoesNotExist):
            send_course_email(100, 101, [], {}, False)

    def test_no_course_title(self):
        entry = InstructorTaskFactory.create(task_key='', task_id='dummy')
        with self.assertRaises(KeyError):
            send_course_email(entry.id, 101, [], {}, False)

    def test_no_course_email_obj(self):
        # Make sure send_course_email handles CourseEmail.DoesNotExist exception.
        entry = InstructorTaskFactory.create(task_key='', task_id='dummy')
        with self.assertRaises(CourseEmail.DoesNotExist):
            send_course_email(entry.id, 101, [], {'course_title': 'Test'}, False)
