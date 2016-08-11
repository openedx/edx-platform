# -*- coding: utf-8 -*-
"""
Unit tests for handling email sending errors
"""
from itertools import cycle

from celery.states import SUCCESS, RETRY  # pylint: disable=no-name-in-module, import-error
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db import DatabaseError
import json
from mock import patch, Mock
from nose.plugins.attrib import attr
from smtplib import SMTPDataError, SMTPServerDisconnected, SMTPConnectError

from bulk_email.models import CourseEmail, SEND_TO_MYSELF, BulkEmailFlag
from bulk_email.tasks import perform_delegate_email_batches, send_course_email
from instructor_task.models import InstructorTask
from instructor_task.subtasks import (
    initialize_subtask_info,
    SubtaskStatus,
    check_subtask_is_valid,
    update_subtask_status,
    DuplicateTaskException,
    MAX_DATABASE_LOCK_RETRIES,
)
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class EmailTestException(Exception):
    """Mock exception for email testing."""
    pass


@attr(shard=1)
@patch('bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
class TestEmailErrors(ModuleStoreTestCase):
    """
    Test that errors from sending email are handled properly.
    """

    ENABLED_CACHES = ['default', 'mongo_metadata_inheritance', 'loc_cache']

    def setUp(self):
        super(TestEmailErrors, self).setUp()
        course_title = u"ẗëṡẗ title ｲ乇丂ｲ ﾶ乇丂丂ﾑg乇 ｷo尺 ﾑﾚﾚ тэѕт мэѕѕаБэ"
        self.course = CourseFactory.create(display_name=course_title)
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.send_mail_url = reverse('send_email', kwargs={'course_id': self.course.id.to_deprecated_string()})
        self.success_content = {
            'course_id': self.course.id.to_deprecated_string(),
            'success': True,
        }

    @classmethod
    def setUpClass(cls):
        super(TestEmailErrors, cls).setUpClass()
        BulkEmailFlag.objects.create(enabled=True, require_course_email_auth=False)

    @classmethod
    def tearDownClass(cls):
        super(TestEmailErrors, cls).tearDownClass()
        BulkEmailFlag.objects.all().delete()

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_data_err_retry(self, retry, get_conn):
        """
        Test that celery handles transient SMTPDataErrors by retrying.
        """
        get_conn.return_value.send_messages.side_effect = SMTPDataError(455, "Throttling: Sending rate exceeded")
        test_email = {
            'action': 'Send email',
            'send_to': '["myself"]',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # Test that we retry upon hitting a 4xx error
        self.assertTrue(retry.called)
        (__, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertIsInstance(exc, SMTPDataError)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.update_subtask_status')
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_data_err_fail(self, retry, result, get_conn):
        """
        Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        """
        # have every fourth email fail due to blacklisting:
        get_conn.return_value.send_messages.side_effect = cycle([SMTPDataError(554, "Email address is blacklisted"),
                                                                 None, None, None])
        # Don't forget to account for the "myself" instructor user
        students = [UserFactory() for _ in xrange(settings.BULK_EMAIL_EMAILS_PER_TASK - 1)]
        for student in students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        test_email = {
            'action': 'Send email',
            'send_to': '["myself", "staff", "learners"]',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        # We shouldn't retry when hitting a 5xx error
        self.assertFalse(retry.called)
        # Test that after the rejected email, the rest still successfully send
        ((_entry_id, _current_task_id, subtask_status), _kwargs) = result.call_args
        self.assertEquals(subtask_status.skipped, 0)
        expected_fails = int((settings.BULK_EMAIL_EMAILS_PER_TASK + 3) / 4.0)
        self.assertEquals(subtask_status.failed, expected_fails)
        self.assertEquals(subtask_status.succeeded, settings.BULK_EMAIL_EMAILS_PER_TASK - expected_fails)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_disconn_err_retry(self, retry, get_conn):
        """
        Test that celery handles SMTPServerDisconnected by retrying.
        """
        get_conn.return_value.open.side_effect = SMTPServerDisconnected(425, "Disconnecting")
        test_email = {
            'action': 'Send email',
            'send_to': '["myself"]',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertTrue(retry.called)
        (__, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertIsInstance(exc, SMTPServerDisconnected)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_conn_err_retry(self, retry, get_conn):
        """
        Test that celery handles SMTPConnectError by retrying.
        """
        get_conn.return_value.open.side_effect = SMTPConnectError(424, "Bad Connection")

        test_email = {
            'action': 'Send email',
            'send_to': '["myself"]',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        response = self.client.post(self.send_mail_url, test_email)
        self.assertEquals(json.loads(response.content), self.success_content)

        self.assertTrue(retry.called)
        (__, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertIsInstance(exc, SMTPConnectError)

    @patch('bulk_email.tasks.SubtaskStatus.increment')
    @patch('bulk_email.tasks.log')
    def test_nonexistent_email(self, mock_log, result):
        """
        Tests retries when the email doesn't exist
        """
        # create an InstructorTask object to pass through
        course_id = self.course.id
        entry = InstructorTask.create(course_id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": -1}
        with self.assertRaises(CourseEmail.DoesNotExist):
            perform_delegate_email_batches(entry.id, course_id, task_input, "action_name")
        ((log_str, __, email_id), __) = mock_log.warning.call_args
        self.assertTrue(mock_log.warning.called)
        self.assertIn('Failed to get CourseEmail with id', log_str)
        self.assertEqual(email_id, -1)
        self.assertFalse(result.called)

    def test_nonexistent_course(self):
        """
        Tests exception when the course in the email doesn't exist
        """
        course_id = SlashSeparatedCourseKey("I", "DONT", "EXIST")
        email = CourseEmail(course_id=course_id)
        email.save()
        entry = InstructorTask.create(course_id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": email.id}
        # (?i) is a regex for ignore case
        with self.assertRaisesRegexp(ValueError, r"(?i)course not found"):
            perform_delegate_email_batches(entry.id, course_id, task_input, "action_name")

    def test_nonexistent_to_option(self):
        """
        Tests exception when the to_option in the email doesn't exist
        """
        with self.assertRaisesRegexp(ValueError, 'Course email being sent to unrecognized target: "IDONTEXIST" *'):
            email = CourseEmail.create(  # pylint: disable=unused-variable
                self.course.id,
                self.instructor,
                ["IDONTEXIST"],
                "re: subject",
                "dummy body goes here"
            )

    def test_nonexistent_cohort(self):
        """
        Tests exception when the cohort doesn't exist
        """
        with self.assertRaisesRegexp(ValueError, 'Cohort IDONTEXIST does not exist *'):
            email = CourseEmail.create(  # pylint: disable=unused-variable
                self.course.id,
                self.instructor,
                ["cohort:IDONTEXIST"],
                "re: subject",
                "dummy body goes here"
            )

    def test_wrong_course_id_in_task(self):
        """
        Tests exception when the course_id in task is not the same as one explicitly passed in.
        """
        email = CourseEmail.create(
            self.course.id,
            self.instructor,
            [SEND_TO_MYSELF],
            "re: subject",
            "dummy body goes here"
        )
        entry = InstructorTask.create("bogus/task/id", "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": email.id}
        with self.assertRaisesRegexp(ValueError, 'does not match task value'):
            perform_delegate_email_batches(entry.id, self.course.id, task_input, "action_name")

    def test_wrong_course_id_in_email(self):
        """
        Tests exception when the course_id in CourseEmail is not the same as one explicitly passed in.
        """
        email = CourseEmail.create(
            SlashSeparatedCourseKey("bogus", "course", "id"),
            self.instructor,
            [SEND_TO_MYSELF],
            "re: subject",
            "dummy body goes here"
        )
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": email.id}
        with self.assertRaisesRegexp(ValueError, 'does not match email value'):
            perform_delegate_email_batches(entry.id, self.course.id, task_input, "action_name")

    def test_send_email_undefined_subtask(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        subtask_id = "subtask-id-value"
        subtask_status = SubtaskStatus.create(subtask_id)
        email_id = 1001
        with self.assertRaisesRegexp(DuplicateTaskException, 'unable to find subtasks of instructor task'):
            send_course_email(entry_id, email_id, to_list, global_email_context, subtask_status.to_dict())

    def test_send_email_missing_subtask(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        subtask_id = "subtask-id-value"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        different_subtask_id = "bogus-subtask-id-value"
        subtask_status = SubtaskStatus.create(different_subtask_id)
        bogus_email_id = 1001
        with self.assertRaisesRegexp(DuplicateTaskException, 'unable to find status for subtask of instructor task'):
            send_course_email(entry_id, bogus_email_id, to_list, global_email_context, subtask_status.to_dict())

    def test_send_email_completed_subtask(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        subtask_id = "subtask-id-value"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        subtask_status = SubtaskStatus.create(subtask_id, state=SUCCESS)
        update_subtask_status(entry_id, subtask_id, subtask_status)
        bogus_email_id = 1001
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        new_subtask_status = SubtaskStatus.create(subtask_id)
        with self.assertRaisesRegexp(DuplicateTaskException, 'already completed'):
            send_course_email(entry_id, bogus_email_id, to_list, global_email_context, new_subtask_status.to_dict())

    def test_send_email_running_subtask(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        subtask_id = "subtask-id-value"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        subtask_status = SubtaskStatus.create(subtask_id)
        update_subtask_status(entry_id, subtask_id, subtask_status)
        check_subtask_is_valid(entry_id, subtask_id, subtask_status)
        bogus_email_id = 1001
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        with self.assertRaisesRegexp(DuplicateTaskException, 'already being executed'):
            send_course_email(entry_id, bogus_email_id, to_list, global_email_context, subtask_status.to_dict())

    def test_send_email_retried_subtask(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        subtask_id = "subtask-id-value"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        subtask_status = SubtaskStatus.create(subtask_id, state=RETRY, retried_nomax=2)
        update_subtask_status(entry_id, subtask_id, subtask_status)
        bogus_email_id = 1001
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        # try running with a clean subtask:
        new_subtask_status = SubtaskStatus.create(subtask_id)
        with self.assertRaisesRegexp(DuplicateTaskException, 'already retried'):
            send_course_email(entry_id, bogus_email_id, to_list, global_email_context, new_subtask_status.to_dict())
        # try again, with a retried subtask with lower count:
        new_subtask_status = SubtaskStatus.create(subtask_id, state=RETRY, retried_nomax=1)
        with self.assertRaisesRegexp(DuplicateTaskException, 'already retried'):
            send_course_email(entry_id, bogus_email_id, to_list, global_email_context, new_subtask_status.to_dict())

    def test_send_email_with_locked_instructor_task(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        subtask_id = "subtask-id-locked-model"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        subtask_status = SubtaskStatus.create(subtask_id)
        bogus_email_id = 1001
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        with patch('instructor_task.subtasks.InstructorTask.save') as mock_task_save:
            mock_task_save.side_effect = DatabaseError
            with self.assertRaises(DatabaseError):
                send_course_email(entry_id, bogus_email_id, to_list, global_email_context, subtask_status.to_dict())
            self.assertEquals(mock_task_save.call_count, MAX_DATABASE_LOCK_RETRIES)

    def test_send_email_undefined_email(self):
        # test at a lower level, to ensure that the course gets checked down below too.
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        entry_id = entry.id
        to_list = ['test@test.com']
        global_email_context = {'course_title': 'dummy course'}
        subtask_id = "subtask-id-undefined-email"
        initialize_subtask_info(entry, "emailed", 100, [subtask_id])
        subtask_status = SubtaskStatus.create(subtask_id)
        bogus_email_id = 1001
        with self.assertRaises(CourseEmail.DoesNotExist):
            # we skip the call that updates subtask status, since we've not set up the InstructorTask
            # for the subtask, and it's not important to the test.
            with patch('bulk_email.tasks.update_subtask_status'):
                send_course_email(entry_id, bogus_email_id, to_list, global_email_context, subtask_status.to_dict())
