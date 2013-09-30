"""
Unit tests for LMS instructor-initiated background tasks.

Runs tasks on answers to course problems to validate that code
paths actually work.

"""
import json
from uuid import uuid4
from itertools import cycle
from mock import patch, Mock
from smtplib import SMTPDataError, SMTPServerDisconnected

from celery.states import SUCCESS

# from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command

from bulk_email.models import CourseEmail, SEND_TO_ALL

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

    def _run_task_with_mock_celery(self, task_class, entry_id, task_id, expected_failure_message=None):
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

    def _test_run_with_task(self, task_class, action_name, total, succeeded, failed=0, skipped=0):
        """Run a task and check the number of emails processed."""
        task_entry = self._create_input_entry()
        parent_status = self._run_task_with_mock_celery(task_class, task_entry.id, task_entry.task_id)
        # check return value
        self.assertEquals(parent_status.get('total'), total)
        self.assertEquals(parent_status.get('action_name'), action_name)
        # compare with entry in table:
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

    def test_successful(self):
        num_students = settings.EMAILS_PER_TASK
        self._create_students(num_students)
        # we also send email to the instructor:
        num_emails = num_students + 1
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            get_conn.return_value.send_messages.side_effect = cycle([None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, num_emails)

    def test_data_err_fail(self):
        # Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        num_students = settings.EMAILS_PER_TASK
        self._create_students(num_students)
        # we also send email to the instructor:
        num_emails = num_students + 1
        expected_fails = int((num_emails + 3) / 4.0)
        expected_succeeds = num_emails - expected_fails
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # have every fourth email fail due to blacklisting:
            get_conn.return_value.send_messages.side_effect = cycle([SMTPDataError(554, "Email address is blacklisted"),
                                                                     None, None, None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, expected_succeeds, failed=expected_fails)

    def test_retry_after_limited_retry_error(self):
        # Test that celery handles connection failures by retrying.
        num_students = 1
        self._create_students(num_students)
        # we also send email to the instructor:
        num_emails = num_students + 1
        expected_fails = 0
        expected_succeeds = num_emails
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # have every other mail attempt fail due to disconnection:
            get_conn.return_value.send_messages.side_effect = cycle([SMTPServerDisconnected(425, "Disconnecting"), None])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, expected_succeeds, failed=expected_fails)

    def test_max_retry(self):
        # Test that celery can hit a maximum number of retries.
        num_students = 1
        self._create_students(num_students)
        # we also send email to the instructor:
        num_emails = num_students + 1
        # This is an ugly hack:  the failures that are reported by the EAGER version of retry
        # are multiplied by the attempted number of retries (equals max plus one).
        expected_fails = num_emails * (settings.BULK_EMAIL_MAX_RETRIES + 1)
        expected_succeeds = 0
        with patch('bulk_email.tasks.get_connection', autospec=True) as get_conn:
            # always fail to connect, triggering repeated retries until limit is hit:
            get_conn.return_value.send_messages.side_effect = cycle([SMTPServerDisconnected(425, "Disconnecting")])
            self._test_run_with_task(send_bulk_course_email, 'emailed', num_emails, expected_succeeds, failed=expected_fails)
