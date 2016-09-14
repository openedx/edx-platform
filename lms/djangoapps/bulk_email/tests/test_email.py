# -*- coding: utf-8 -*-
"""
Unit tests for sending course email
"""
import json
from mock import patch, Mock
from nose.plugins.attrib import attr
import os
from unittest import skipIf

from django.conf import settings
from django.core import mail
from django.core.urlresolvers import reverse
from django.core.management import call_command
from django.test.utils import override_settings

from instructor_email_widget.models import StudentsForQuery, TemporaryQuery
from bulk_email.models import Optout
from courseware.models import StudentModule
from courseware.tests.factories import StaffFactory, InstructorFactory
from instructor_task.subtasks import update_subtask_status
from student.roles import CourseStaffRole
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory, UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

STAFF_COUNT = 3
STUDENT_COUNT = 10
LARGE_NUM_EMAILS = 137


class MockCourseEmailResult(object):
    """
    A small closure-like class to keep count of emails sent over all tasks, recorded
    by mock object side effects
    """
    emails_sent = 0

    def get_mock_update_subtask_status(self):
        """Wrapper for mock email function."""
        def mock_update_subtask_status(entry_id, current_task_id, new_subtask_status):
            """Increments count of number of emails sent."""
            self.emails_sent += new_subtask_status.succeeded
            return update_subtask_status(entry_id, current_task_id, new_subtask_status)
        return mock_update_subtask_status


class EmailSendFromDashboardTestCase(ModuleStoreTestCase):
    """
    Test that emails send correctly.
    """

    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
    def setUp(self):
        super(EmailSendFromDashboardTestCase, self).setUp()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(display_name=course_title)

        self.instructor = InstructorFactory(course_key=self.course.id)

        # Create staff
        self.staff = [StaffFactory(course_key=self.course.id)
                      for _ in xrange(STAFF_COUNT)]

        # Create students
        self.students = [UserFactory() for _ in xrange(STUDENT_COUNT)]
        for student in self.students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

        self.client.login(username=self.instructor.username, password="test")

        # Pull up email view on instructor dashboard
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        # Response loads the whole instructor dashboard, so no need to explicitly
        # navigate to a particular email section
        response = self.client.get(self.url)
        email_section = '<div class="vert-left send-email" id="section-send-email">'
        # If this fails, it is likely because ENABLE_INSTRUCTOR_EMAIL is set to False
        self.assertTrue(email_section in response.content)
        self.send_mail_url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.success_content = {
            'course_id': self.course.id.to_deprecated_string(),
            'success': True,
        }


@attr('shard_1')
@patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message'))
class TestEmailSendFromDashboardMockedHtmlToText(EmailSendFromDashboardTestCase):
    """
    Tests email sending with mocked html_to_text.
    """
    @patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': True})
    def test_email_disabled(self):
        """
        Test response when email is disabled for course.
        """
        test_email = {
            'action': 'Send email',
            'send_to': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        # We should get back a HttpResponseForbidden (status code 403)
        self.assertContains(response, "Email is not enabled for this course.", status_code=403)

    @patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message'))
    def test_send_to_self(self):
        """
        Make sure email send to myself goes to myself.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'send',
            'send_to': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # Check that outbox is as expected
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(len(mail.outbox[0].to), 1)
        self.assertEquals(mail.outbox[0].to[0], self.instructor.email)
        self.assertEquals(mail.outbox[0].subject, 'test subject for myself')

    def test_send_to_staff(self):
        """
        Make sure email send to staff and instructors goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.
        test_email = {
            'action': 'Send email',
            'send_to': 'staff',
            'subject': 'test subject for staff',
            'message': 'test message for subject'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

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
            'send_to': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # the 1 is for the instructor
        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    def _setup_query(self):
        """
        Helper function for email to query tests
        """
        self.problem = self.course.id.make_usage_key('problem', '123')
        self._make_query('opened')
        temp_ids = self._get_temp_query_ids()
        self._save_query(temp_ids)
        saved_queries = self._get_saved_queries()
        self.assertEquals(len(saved_queries), 1)
        return saved_queries[0]['group']

    def test_send_to_query(self):
        """
        Make sure email send to query goes there.
        """
        query_id = self._setup_query()
        StudentModule.objects.create(
            student=self.students[0],
            course_id=self.course.id,
            module_state_key=self.problem,
        )
        test_email = {
            'action': 'Send email',
            'send_to': query_id,
            'subject': 'test subject for query',
            'message': 'test message for all',
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to[0], self.students[0].email)

        students_left = StudentsForQuery.objects.all()
        queries_left = TemporaryQuery.objects.all()
        self.assertEquals(len(students_left), 0)
        self.assertEquals(len(queries_left), 1)  # should just have the one created from _setup_query

    def test_send_to_query_no_results(self):
        """
        Make sure email send to query with no results handles successfully.
        """
        query_id = self._setup_query()
        test_email = {
            'action': 'Send email',
            'send_to': query_id,
            'subject': 'test subject for query',
            'message': 'test message for all',
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)
        self.assertEquals(len(mail.outbox), 0)

        queries_left = TemporaryQuery.objects.all()
        self.assertEquals(len(queries_left), 1)  # should just have the one created from _setup_query

    def _make_query(self, query_type, joining="OR"):
        """
        Issues a query to the backend
        """
        url = reverse('get_single_query', kwargs={'course_id': self.course.id})
        function_args = [joining, 'Problem', self.problem.block_type, self.problem.block_id]
        single_args = {
            'filter': query_type,
            "entityName": 'Introduction',
        }
        encoded_args = '/'.join(function_args)
        query_url = '/'.join([url, encoded_args])
        _unused_response = self.client.get(query_url, single_args)

    def _get_temp_query_ids(self):
        """
        Returns all the current queries
        """
        get_temp_url = reverse('get_temp_queries', kwargs={'course_id': self.course.id})
        temp_response = self.client.get(get_temp_url)
        queries = json.loads(temp_response.content)['queries']
        prev_query_ids = [
            str(query['id'])
            for query in queries
        ]
        return prev_query_ids

    def _save_query(self, existing):
        """
        Save a grouped query
        """
        save_url = reverse('save_query', kwargs={'course_id': self.course.id})
        save_args = {
            'existing': ','.join(existing),
        }
        response = self.client.post(save_url, save_args)
        return response

    def _get_saved_queries(self):
        """
        Retrieve saved group queries
        """
        get_saved_url = reverse('get_saved_queries', kwargs={'course_id': self.course.id})
        temp_response = self.client.get(get_saved_url)
        queries = json.loads(temp_response.content)['queries']
        return queries

    @override_settings(BULK_EMAIL_JOB_SIZE_THRESHOLD=1)
    def test_send_to_all_high_queue(self):
        """
        Test that email is still sent when the high priority queue is used
        """
        self.test_send_to_all()

    def test_no_duplicate_emails_staff_instructor(self):
        """
        Test that no duplicate emails are sent to a course instructor that is
        also course staff
        """
        CourseStaffRole(self.course.id).add_users(self.instructor)
        self.test_send_to_all()

    def test_no_duplicate_emails_enrolled_staff(self):
        """
        Test that no duplicate emails are sent to a course instructor that is
        also enrolled in the course
        """
        CourseEnrollment.enroll(self.instructor, self.course.id)
        self.test_send_to_all()

    def test_no_duplicate_emails_unenrolled_staff(self):
        """
        Test that no duplicate emails are sent to a course staff that is
        not enrolled in the course, but is enrolled in other courses
        """
        course_1 = CourseFactory.create()
        course_2 = CourseFactory.create()
        # make sure self.instructor isn't enrolled in the course
        self.assertFalse(CourseEnrollment.is_enrolled(self.instructor, self.course.id))
        CourseEnrollment.enroll(self.instructor, course_1.id)
        CourseEnrollment.enroll(self.instructor, course_2.id)
        self.test_send_to_all()

    def test_unicode_subject_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        uni_subject = u'téśt śúbjéćt főŕ áĺĺ'
        test_email = {
            'action': 'Send email',
            'send_to': 'all',
            'subject': uni_subject,
            'message': 'test message for all'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )
        self.assertEquals(mail.outbox[0].subject, uni_subject)

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
            'send_to': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))

        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

    @override_settings(BULK_EMAIL_EMAILS_PER_TASK=3)
    @patch('bulk_email.tasks.update_subtask_status')
    def test_chunked_queries_send_numerous_emails(self, email_mock):
        """
        Test sending a large number of emails, to test the chunked querying
        """
        mock_factory = MockCourseEmailResult()
        email_mock.side_effect = mock_factory.get_mock_update_subtask_status()
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
            'send_to': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(mock_factory.emails_sent,
                          1 + len(self.staff) + len(self.students) + LARGE_NUM_EMAILS - len(optouts))
        outbox_contents = [e.to[0] for e in mail.outbox]
        should_send_contents = ([self.instructor.email] +
                                [s.email for s in self.staff] +
                                [s.email for s in self.students] +
                                [s.email for s in added_users if s not in optouts])
        self.assertItemsEqual(outbox_contents, should_send_contents)


@attr('shard_1')
@patch.dict(settings.FEATURES, {'ENABLE_INSTRUCTOR_EMAIL': True, 'REQUIRE_COURSE_EMAIL_AUTH': False})
@skipIf(os.environ.get("TRAVIS") == 'true', "Skip this test in Travis CI.")
class TestEmailSendFromDashboard(EmailSendFromDashboardTestCase):
    """
    Tests email sending without mocked html_to_text.

    Note that these tests are skipped on Travis because we can't use the
    function `html_to_text` as it is currently implemented on Travis.
    """

    def test_unicode_message_send_to_all(self):
        """
        Make sure email (with Unicode characters) send to all goes there.
        """
        # Now we know we have pulled up the instructor dash's email view
        # (in the setUp method), we can test sending an email.

        uni_message = u'ẗëṡẗ ṁëṡṡäġë ḟöṛ äḷḷ ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ fоѓ аll'
        test_email = {
            'action': 'Send email',
            'send_to': 'all',
            'subject': 'test subject for all',
            'message': uni_message
        }
        # Post the email to the instructor dashboard API
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertEquals(len(mail.outbox), 1 + len(self.staff) + len(self.students))
        self.assertItemsEqual(
            [e.to[0] for e in mail.outbox],
            [self.instructor.email] + [s.email for s in self.staff] + [s.email for s in self.students]
        )

        message_body = mail.outbox[0].body
        self.assertIn(uni_message, message_body)
