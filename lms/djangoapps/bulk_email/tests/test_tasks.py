# -*- coding: utf-8 -*-
"""
Unit tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""


import json
from itertools import chain, cycle, repeat
from smtplib import SMTPAuthenticationError, SMTPConnectError, SMTPDataError, SMTPServerDisconnected
from uuid import uuid4

from boto.exception import AWSConnectionError
from boto.ses.exceptions import (
    SESAddressBlacklistedError,
    SESAddressNotVerifiedError,
    SESDailyQuotaExceededError,
    SESDomainEndsWithDotError,
    SESDomainNotConfirmedError,
    SESIdentityNotVerifiedError,
    SESIllegalAddressError,
    SESLocalAddressCharacterError,
    SESMaxSendingRateExceededError
)
from celery.states import FAILURE, SUCCESS
from django.conf import settings
from django.core.management import call_command
from mock import Mock, patch
from opaque_keys.edx.locator import CourseLocator
from six.moves import range

from ..models import SEND_TO_LEARNERS, SEND_TO_MYSELF, SEND_TO_STAFF, CourseEmail, Optout
from lms.djangoapps.bulk_email.tasks import _get_course_email_context
from lms.djangoapps.instructor_task.models import InstructorTask
from lms.djangoapps.instructor_task.subtasks import SubtaskStatus, update_subtask_status
from lms.djangoapps.instructor_task.tasks import send_bulk_course_email
from lms.djangoapps.instructor_task.tests.factories import InstructorTaskFactory
from lms.djangoapps.instructor_task.tests.test_base import InstructorTaskCourseTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestTaskFailure(Exception):
    """Dummy exception used for unit tests."""
    pass


def my_update_subtask_status(entry_id, current_task_id, new_subtask_status):
    """
    Check whether a subtask has been updated before really updating.

    Check whether a subtask which has been retried
    has had the retry already write its results here before the code
    that was invoking the retry had a chance to update this status.

    This is the norm in "eager" mode (used by tests) where the retry is called
    and run to completion before control is returned to the code that
    invoked the retry.  If the retries eventually end in failure (e.g. due to
    a maximum number of retries being attempted), the "eager" code will return
    the error for each retry as it is popped off the stack.  We want to just ignore
    the later updates that are called as the result of the earlier retries.

    This should not be an issue in production, where status is updated before
    a task is retried, and is then updated afterwards if the retry fails.
    """
    entry = InstructorTask.objects.get(pk=entry_id)
    subtask_dict = json.loads(entry.subtasks)
    subtask_status_info = subtask_dict['status']
    current_subtask_status = SubtaskStatus.from_dict(subtask_status_info[current_task_id])
    current_retry_count = current_subtask_status.get_retry_count()
    new_retry_count = new_subtask_status.get_retry_count()
    if current_retry_count <= new_retry_count:
        update_subtask_status(entry_id, current_task_id, new_subtask_status)


@patch('lms.djangoapps.bulk_email.models.html_to_text', Mock(return_value='Mocking CourseEmail.text_message', autospec=True))
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
        targets = [SEND_TO_MYSELF, SEND_TO_STAFF, SEND_TO_LEARNERS]
        course_id = course_id or self.course.id
        course_email = CourseEmail.create(
            course_id, self.instructor, targets, "Test Subject", "<p>This is a test message</p>"
        )
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
        """Mock was not needed for some tests, testing to see if it's needed at all."""
        task_args = [entry_id, {}]
        return task_class.apply(task_args, task_id=task_id).get()

    def test_email_missing_current_task(self):
        task_entry = self._create_input_entry()
        with self.assertRaises(ValueError):
            send_bulk_course_email(task_entry.id, {})

    def test_email_undefined_course(self):
        # Check that we fail when passing in a course that doesn't exist.
        task_entry = self._create_input_entry(course_id=CourseLocator("bogus", "course", "id"))
        with self.assertRaises(ValueError):
            self._run_task_with_mock_celery(send_bulk_course_email, task_entry.id, task_entry.task_id)

    def test_bad_task_id_on_update(self):
        task_entry = self._create_input_entry()

        def dummy_update_subtask_status(entry_id, _current_task_id, new_subtask_status):
            """Passes a bad value for task_id to test update_subtask_status"""
            bogus_task_id = "this-is-bogus"
            update_subtask_status(entry_id, bogus_task_id, new_subtask_status)

        with self.assertRaises(ValueError):
            with patch('lms.djangoapps.bulk_email.tasks.update_subtask_status', dummy_update_subtask_status):
                send_bulk_course_email(task_entry.id, {})

    def _create_students(self, num_students):
        """Create students for testing"""
        return [self.create_student('robot%d' % i) for i in range(num_students)]

    def _assert_single_subtask_status(self, entry, succeeded, failed=0, skipped=0, retried_nomax=0, retried_withmax=0):
        """Compare counts with 'subtasks' entry in InstructorTask table."""
        subtask_info = json.loads(entry.subtasks)
        # verify subtask-level counts:
        self.assertEqual(subtask_info.get('total'), 1)
        self.assertEqual(subtask_info.get('succeeded'), 1 if succeeded > 0 else 0)
        self.assertEqual(subtask_info.get('failed'), 0 if succeeded > 0 else 1)
        # verify individual subtask status:
        subtask_status_info = subtask_info.get('status')
        task_id_list = list(subtask_status_info.keys())
        self.assertEqual(len(task_id_list), 1)
        task_id = task_id_list[0]
        subtask_status = subtask_status_info.get(task_id)
        print(u"Testing subtask status: {}".format(subtask_status))
        self.assertEqual(subtask_status.get('task_id'), task_id)
        self.assertEqual(subtask_status.get('attempted'), succeeded + failed)
        self.assertEqual(subtask_status.get('succeeded'), succeeded)
        self.assertEqual(subtask_status.get('skipped'), skipped)
        self.assertEqual(subtask_status.get('failed'), failed)
        self.assertEqual(subtask_status.get('retried_nomax'), retried_nomax)
        self.assertEqual(subtask_status.get('retried_withmax'), retried_withmax)
        self.assertEqual(subtask_status.get('state'), SUCCESS if succeeded > 0 else FAILURE)

    def _test_run_with_task(
            self, task_class, action_name, total, succeeded,
            failed=0, skipped=0, retried_nomax=0, retried_withmax=0):
        """Run a task and check the number of emails processed."""
        task_entry = self._create_input_entry()
        parent_status = self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)

        # check return value
        self.assertEqual(parent_status.get('total'), total)
        self.assertEqual(parent_status.get('action_name'), action_name)

        # compare with task_output entry in InstructorTask table:
        entry = InstructorTask.objects.get(id=task_entry.id)
        status = json.loads(entry.task_output)
        self.assertEqual(status.get('attempted'), succeeded + failed)
        self.assertEqual(status.get('succeeded'), succeeded)
        self.assertEqual(status.get('skipped'), skipped)
        self.assertEqual(status.get('failed'), failed)
        self.assertEqual(status.get('total'), total)
        self.assertEqual(status.get('action_name'), action_name)
        self.assertGreater(status.get('duration_ms'), 0)
        self.assertEqual(entry.task_state, SUCCESS)
        self._assert_single_subtask_status(entry, succeeded, failed, skipped, retried_nomax, retried_withmax)
        return entry

    def test_successful(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.BULK_EMAIL_EMAILS_PER_TASK
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, num_emails)

    def test_successful_twice(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.BULK_EMAIL_EMAILS_PER_TASK
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            task_entry = self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, num_emails)

        # submit the same task a second time, and confirm that it is not run again.
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([Exception("This should not happen!")])
            parent_status = self._run_task_with_mock_celery(send_bulk_course_email, task_entry.id, task_entry.task_id)
        self.assertEqual(parent_status.get('total'), num_emails)
        self.assertEqual(parent_status.get('succeeded'), num_emails)
        self.assertEqual(parent_status.get('failed'), 0)

    def test_unactivated_user(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.BULK_EMAIL_EMAILS_PER_TASK
        # We also send email to the instructor:
        students = self._create_students(num_emails - 1)
        # mark a student as not yet having activated their email:
        student = students[0]
        student.is_active = False
        student.save()
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails - 1, num_emails - 1)

    def test_skipped(self):
        # Select number of emails to fit into a single subtask.
        num_emails = settings.BULK_EMAIL_EMAILS_PER_TASK
        # We also send email to the instructor:
        students = self._create_students(num_emails - 1)
        # have every fourth student optout:
        expected_skipped = int((num_emails + 3) / 4.0)
        expected_succeeds = num_emails - expected_skipped
        for index in range(0, num_emails, 4):
            Optout.objects.create(user=students[index], course_id=self.course.id)
        # mark some students as opting out
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(
                send_bulk_course_email, 'emailed', num_emails, expected_succeeds, skipped=expected_skipped
            )

    def _test_email_address_failures(self, exception):
        """Test that celery handles bad address errors by failing and not retrying."""
        # Select number of emails to fit into a single subtask.
        num_emails = settings.BULK_EMAIL_EMAILS_PER_TASK
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = int((num_emails + 3) / 4.0)
        expected_succeeds = num_emails - expected_fails
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # have every fourth email fail due to some address failure:
            get_conn.return_value.send_messages.side_effect = cycle([exception, None, None, None])
            self._test_run_with_task(
                send_bulk_course_email, 'emailed', num_emails, expected_succeeds, failed=expected_fails
            )

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

    def test_ses_domain_ends_with_dot(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        self._test_email_address_failures(SESDomainEndsWithDotError(554, "Email address ends with a dot"))

    def test_bulk_email_skip_with_non_ascii_emails(self):
        """
        Tests that bulk email skips the email address containing non-ASCII characters
        and does not fail.
        """
        num_emails = 10
        emails_with_non_ascii_chars = 3
        num_of_course_instructors = 1

        students = [self.create_student('robot%d' % i) for i in range(num_emails)]
        for student in students[:emails_with_non_ascii_chars]:
            student.email = '{username}@tesá.com'.format(username=student.username)
            student.save()

        total = num_emails + num_of_course_instructors
        expected_succeeds = num_emails - emails_with_non_ascii_chars + num_of_course_instructors
        expected_fails = emails_with_non_ascii_chars

        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(
                task_class=send_bulk_course_email,
                action_name='emailed',
                total=total,
                succeeded=expected_succeeds,
                failed=expected_fails
            )

    def _test_retry_after_limited_retry_error(self, exception):
        """Test that celery handles connection failures by retrying."""
        # If we want the batch to succeed, we need to send fewer emails
        # than the max retries, so that the max is not triggered.
        num_emails = settings.BULK_EMAIL_MAX_RETRIES
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = 0
        expected_succeeds = num_emails
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
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
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # always fail to connect, triggering repeated retries until limit is hit:
            get_conn.return_value.send_messages.side_effect = cycle([exception])
            with patch('lms.djangoapps.bulk_email.tasks.update_subtask_status', my_update_subtask_status):
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
        self._test_retry_after_limited_retry_error(
            AWSConnectionError("Unable to provide secure connection through proxy")
        )

    def test_max_retry_after_aws_connect_error(self):
        self._test_max_retry_limit_causes_failure(
            AWSConnectionError("Unable to provide secure connection through proxy")
        )

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
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
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
        self._test_retry_after_unlimited_retry_error(
            SESMaxSendingRateExceededError(455, "Throttling: Sending rate exceeded")
        )

    def _test_immediate_failure(self, exception):
        """Test that celery can hit a maximum number of retries."""
        # Doesn't really matter how many recipients, since we expect
        # to fail on the first.
        num_emails = 10
        # We also send email to the instructor:
        self._create_students(num_emails - 1)
        expected_fails = num_emails
        expected_succeeds = 0
        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
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

    def test_failure_on_ses_address_not_verified(self):
        self._test_immediate_failure(SESAddressNotVerifiedError(403, "Who *are* you?"))

    def test_failure_on_ses_identity_not_verified(self):
        self._test_immediate_failure(SESIdentityNotVerifiedError(403, "May I please see an ID!"))

    def test_failure_on_ses_domain_not_confirmed(self):
        self._test_immediate_failure(SESDomainNotConfirmedError(403, "You're out of bounds!"))

    def test_bulk_emails_with_unicode_course_image_name(self):
        # Test bulk email with unicode characters in course image name
        course_image = u'在淡水測試.jpg'
        self.course = CourseFactory.create(course_image=course_image)

        num_emails = 2
        # We also send email to the instructor:
        self._create_students(num_emails - 1)

        with patch('lms.djangoapps.bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, num_emails)

    def test_get_course_email_context_has_correct_keys(self):
        result = _get_course_email_context(self.course)
        self.assertIn('course_title', result)
        self.assertIn('course_root', result)
        self.assertIn('course_language', result)
        self.assertIn('course_url', result)
        self.assertIn('course_image_url', result)
        self.assertIn('course_end_date', result)
        self.assertIn('account_settings_url', result)
        self.assertIn('email_settings_url', result)
        self.assertIn('platform_name', result)
