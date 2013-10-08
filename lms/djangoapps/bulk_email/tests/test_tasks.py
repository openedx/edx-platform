"""
Unit tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import json
from uuid import uuid4
from itertools import cycle, chain, repeat
from mock import patch, Mock
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError, SMTPAuthenticationError
from boto.ses.exceptions import (
    SESDailyQuotaExceededError,
    SESMaxSendingRateExceededError,
    SESAddressBlacklistedError,
    SESIllegalAddressError,
    SESLocalAddressCharacterError,
)
from boto.exception import AWSConnectionError

from celery.states import SUCCESS, FAILURE

# from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command

from bulk_email.models import CourseEmail, Optout, SEND_TO_ALL

# from instructor_task.tests.test_tasks import TestInstructorTasks
from instructor_task.tasks import send_bulk_course_email
from instructor_task.models import InstructorTask
from instructor_task.tests.test_base import InstructorTaskCourseTestCase
from instructor_task.tests.factories import InstructorTaskFactory


class TestTaskFailure(Exception):
    """Dummy exception used for unit tests."""
    pass


class TestBulkEmailInstructorTask(InstructorTaskCourseTestCase):
    """Tests instructor task that send bulk email."""

    def setUp(self):
        super(TestBulkEmailInstructorTask, self).setUp()
        self.initialize_course()
        self.instructor = self.create_instructor('instructor')

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")

    def _create_input_entry(self, course_id=None):
        """
        Creates a InstructorTask entry for testing.

        Overrides the base class version in that this creates CourseEmail.
        """
        to_option = SEND_TO_ALL
        course_id = course_id or self.course.id
        course_email = CourseEmail.create(course_id, self.instructor, to_option, "Test Subject", "<p>This is a test message</p>")
        task_input = {'email_id': course_email.id}
        task_id = str(uuid4())
        instructor_task = InstructorTaskFactory.create(
            course_id=course_id,
            requester=self.instructor,
            task_input=json.dumps(task_input),
            task_key='dummy value',
            task_id=task_id,
        )
        return instructor_task

    def _run_task_with_mock_celery(self, task_class, entry_id, task_id):
        """Submit a task and mock how celery provides a current_task."""
        self.current_task = Mock()
        self.current_task.max_retries = settings.BULK_EMAIL_MAX_RETRIES
        self.current_task.default_retry_delay = settings.BULK_EMAIL_DEFAULT_RETRY_DELAY
        task_args = [entry_id, {}]

        with patch('bulk_email.tasks._get_current_task') as mock_get_task:
            mock_get_task.return_value = self.current_task
            return task_class.apply(task_args, task_id=task_id).get()

    def test_email_missing_current_task(self):
        task_entry = self._create_input_entry()
        with self.assertRaises(ValueError):
            send_bulk_course_email(task_entry.id, {})

    def test_email_undefined_course(self):
        # Check that we fail when passing in a course that doesn't exist.
        task_entry = self._create_input_entry(course_id="bogus/course/id")
        with self.assertRaises(ValueError):
            self._run_task_with_mock_celery(send_bulk_course_email, task_entry.id, task_entry.task_id)

    def _create_students(self, num_students):
        """Create students, a problem, and StudentModule objects for testing"""
        students = [
            self.create_student('robot%d' % i) for i in xrange(num_students)
        ]
        return students

    def _assert_single_subtask_status(self, entry, succeeded, failed=0, skipped=0, retried_nomax=0, retried_withmax=0):
        """Compare counts with 'subtasks' entry in InstructorTask table."""
        subtask_info = json.loads(entry.subtasks)
        # verify subtask-level counts:
        self.assertEquals(subtask_info.get('total'), 1)
        self.assertEquals(subtask_info.get('succeeded'), 1 if succeeded > 0 else 0)
        self.assertEquals(subtask_info['failed'], 0 if succeeded > 0 else 1)
        # self.assertEquals(subtask_info['retried'], retried_nomax + retried_withmax)
        # verify individual subtask status:
        subtask_status_info = subtask_info['status']
        task_id_list = subtask_status_info.keys()
        self.assertEquals(len(task_id_list), 1)
        task_id = task_id_list[0]
        subtask_status = subtask_status_info.get(task_id)
        print("Testing subtask status: {}".format(subtask_status))
        self.assertEquals(subtask_status['task_id'], task_id)
        self.assertEquals(subtask_status['attempted'], succeeded + failed)
        self.assertEquals(subtask_status['succeeded'], succeeded)
        self.assertEquals(subtask_status['skipped'], skipped)
        self.assertEquals(subtask_status['failed'], failed)
        self.assertEquals(subtask_status['retried_nomax'], retried_nomax)
        self.assertEquals(subtask_status['retried_withmax'], retried_withmax)
        self.assertEquals(subtask_status['state'], SUCCESS if succeeded > 0 else FAILURE)

    def _test_run_with_task(self, task_class, action_name, total, succeeded, failed=0, skipped=0, retried_nomax=0, retried_withmax=0):
        """Run a task and check the number of emails processed."""
        task_entry = self._create_input_entry()
        parent_status = self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)

        # check return value
        self.assertEquals(parent_status.get('total'), total)
        self.assertEquals(parent_status.get('action_name'), action_name)

        # compare with task_output entry in InstructorTask table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        status = json.loads(entry.task_output)
        self.assertEquals(status.get('attempted'), succeeded + failed)
        self.assertEquals(status.get('succeeded'), succeeded)
        self.assertEquals(status['skipped'], skipped)
        self.assertEquals(status['failed'], failed)
        self.assertEquals(status.get('total'), total)
        self.assertEquals(status.get('action_name'), action_name)
        self.assertGreater(status.get('duration_ms'), 0)
        self.assertEquals(entry.task_state, SUCCESS)
        self._assert_single_subtask_status(entry, succeeded, failed, skipped, retried_nomax, retried_withmax)

    def test_successful(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.EMAILS_PER_TASK
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, num_emails)

    def test_unactivated_user(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.EMAILS_PER_TASK
        # We also send email to the instructor:
        students = self._create_students(num_emails - 1)
        # mark a student as not yet having activated their email:
        student = students[0]
        student.is_active = False
        student.save()
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails - 1, num_emails - 1)

    def test_skipped(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.EMAILS_PER_TASK
        # We also send email to the instructor:
        students = self._create_students(num_emails - 1)
        # have every fourth student optout:
        expected_skipped = int((num_emails + 3) / 4.0)
        expected_succeeds = num_emails - expected_skipped
        for index in range(0, num_emails, 4):
            Optout.objects.create(user=students[index], course_id=self.course.id)
        # mark some students as opting out
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, expected_succeeds, skipped=expected_skipped)

    def _test_email_address_failures(self, exception):
        """Test that celery handles bad address errors by failing and not retrying."""
        # Select number of emails to fit into a single subtask.
        num_emails = settings.EMAILS_PER_TASK
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = int((num_emails + 3) / 4.0)
        expected_succeeds = num_emails - expected_fails
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # have every fourth email fail due to some address failure:
            get_conn.return_value.send_messages.side_effect = cycle([exception, None, None, None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, expected_succeeds, failed=expected_fails)

    def test_smtp_blacklisted_user(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        self._test_email_address_failures(SMTPDataError(554, "Email address is blacklisted"))

    def test_ses_blacklisted_user(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        self._test_email_address_failures(SESAddressBlacklistedError(554, "Email address is blacklisted"))

    def test_ses_illegal_address(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        self._test_email_address_failures(SESIllegalAddressError(554, "Email address is illegal"))

    def test_ses_local_address_character_error(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        self._test_email_address_failures(SESLocalAddressCharacterError(554, "Email address contains a bad character"))

    def _test_retry_after_limited_retry_error(self, exception):
        """Test that celery handles connection failures by retrying."""
        # If we want the batch to succeed, we need to send fewer emails
        # than the max retries, so that the max is not triggered.
        num_emails = settings.BULK_EMAIL_MAX_RETRIES
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = 0
        expected_succeeds = num_emails
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # Have every other mail attempt fail due to disconnection.
            get_conn.return_value.send_messages.side_effect = cycle([exception, None])
            self._test_run_with_task(
                send_bulk_course_email,
                'emailed',
                num_emails,
                expected_succeeds,
                failed=expected_fails,
                retried_withmax=num_emails
            )

    def _test_max_retry_limit_causes_failure(self, exception):
        """Test that celery can hit a maximum number of retries."""
        # Doesn't really matter how many recipients, since we expect
        # to fail on the first.
        num_emails = 10
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = num_emails
        expected_succeeds = 0
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # always fail to connect, triggering repeated retries until limit is hit:
            get_conn.return_value.send_messages.side_effect = cycle([exception])
            self._test_run_with_task(
                send_bulk_course_email,
                'emailed',
                num_emails,
                expected_succeeds,
                failed=expected_fails,
                retried_withmax=(settings.BULK_EMAIL_MAX_RETRIES + 1)
            )

    def test_retry_after_smtp_disconnect(self):
        self._test_retry_after_limited_retry_error(SMTPServerDisconnected(425, "Disconnecting"))

    def test_max_retry_after_smtp_disconnect(self):
        self._test_max_retry_limit_causes_failure(SMTPServerDisconnected(425, "Disconnecting"))

    def test_retry_after_smtp_connect_error(self):
        self._test_retry_after_limited_retry_error(SMTPConnectError(424, "Bad Connection"))

    def test_max_retry_after_smtp_connect_error(self):
        self._test_max_retry_limit_causes_failure(SMTPConnectError(424, "Bad Connection"))

    def test_retry_after_aws_connect_error(self):
        self._test_retry_after_limited_retry_error(AWSConnectionError("Unable to provide secure connection through proxy"))

    def test_max_retry_after_aws_connect_error(self):
        self._test_max_retry_limit_causes_failure(AWSConnectionError("Unable to provide secure connection through proxy"))

    def test_retry_after_general_error(self):
        self._test_retry_after_limited_retry_error(Exception("This is some random exception."))

    def test_max_retry_after_general_error(self):
        self._test_max_retry_limit_causes_failure(Exception("This is some random exception."))

    def _test_retry_after_unlimited_retry_error(self, exception):
        """Test that celery handles throttling failures by retrying."""
        num_emails = 8
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = 0
        expected_succeeds = num_emails
        # Note that because celery in eager mode will call retries synchronously,
        # each retry will increase the stack depth.  It turns out that there is a
        # maximum depth at which a RuntimeError is raised ("maximum recursion depth
        # exceeded").  The maximum recursion depth is 90, so
        # num_emails * expected_retries < 90.
        expected_retries = 10
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # Cycle through N throttling errors followed by a success.
            get_conn.return_value.send_messages.side_effect = cycle(
                chain(repeat(exception, expected_retries), [None])
            )
            self._test_run_with_task(
                send_bulk_course_email,
                'emailed',
                num_emails,
                expected_succeeds,
                failed=expected_fails,
                retried_nomax=(expected_retries * num_emails)
            )

    def test_retry_after_smtp_throttling_error(self):
        self._test_retry_after_unlimited_retry_error(SMTPDataError(455, "Throttling: Sending rate exceeded"))

    def test_retry_after_ses_throttling_error(self):
        self._test_retry_after_unlimited_retry_error(SESMaxSendingRateExceededError(455, "Throttling: Sending rate exceeded"))

    def _test_immediate_failure(self, exception):
        """Test that celery can hit a maximum number of retries."""
        # Doesn't really matter how many recipients, since we expect
        # to fail on the first.
        num_emails = 10
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = num_emails
        expected_succeeds = 0
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # always fail to connect, triggering repeated retries until limit is hit:
            get_conn.return_value.send_messages.side_effect = cycle([exception])
            self._test_run_with_task(
                send_bulk_course_email,
                'emailed',
                num_emails,
                expected_succeeds,
                failed=expected_fails,
            )

    def test_failure_on_unhandled_smtp(self):
        self._test_immediate_failure(SMTPAuthenticationError(403, "That password doesn't work!"))

    def test_failure_on_ses_quota_exceeded(self):
        self._test_immediate_failure(SESDailyQuotaExceededError(403, "You're done for the day!"))
