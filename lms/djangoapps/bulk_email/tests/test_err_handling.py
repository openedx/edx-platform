"""
Unit tests for handling email sending errors
"""
from itertools import cycle
from mock import patch, Mock
from smtplib import SMTPDataError, SMTPServerDisconnected, SMTPConnectError
from unittest import skip

from django.test.utils import override_settings
from django.conf import settings
from django.core.management import call_command
from django.core.urlresolvers import reverse


from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from student.tests.factories import UserFactory, AdminFactory, CourseEnrollmentFactory

from bulk_email.models import CourseEmail
from bulk_email.tasks import perform_delegate_email_batches
from instructor_task.models import InstructorTask


class EmailTestException(Exception):
    """Mock exception for email testing."""
    pass


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestEmailErrors(ModuleStoreTestCase):
    """
    Test that errors from sending email are handled properly.
    """

    def setUp(self):
        self.course = CourseFactory.create()
        self.instructor = AdminFactory.create()
        self.client.login(username=self.instructor.username, password="test")

        # load initial content (since we don't run migrations as part of tests):
        call_command("loaddata", "course_email_template.json")
        self.url = reverse('instructor_dashboard', kwargs={'course_id': self.course.id})

    def tearDown(self):
        patch.stopall()

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_data_err_retry(self, retry, get_conn):
        """
        Test that celery handles transient SMTPDataErrors by retrying.
        """
        get_conn.return_value.send_messages.side_effect = SMTPDataError(455, "Throttling: Sending rate exceeded")
        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        self.client.post(self.url, test_email)

        # Test that we retry upon hitting a 4xx error
        self.assertTrue(retry.called)
        (_, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertTrue(type(exc) == SMTPDataError)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.create_subtask_result')
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_data_err_fail(self, retry, result, get_conn):
        """
        Test that celery handles permanent SMTPDataErrors by failing and not retrying.
        """
        # have every fourth email fail due to blacklisting:
        get_conn.return_value.send_messages.side_effect = cycle([SMTPDataError(554, "Email address is blacklisted"),
                                                                 None, None, None])
        students = [UserFactory() for _ in xrange(settings.EMAILS_PER_TASK)]
        for student in students:
            CourseEnrollmentFactory.create(user=student, course_id=self.course.id)

        test_email = {
            'action': 'Send email',
            'to_option': 'all',
            'subject': 'test subject for all',
            'message': 'test message for all'
        }
        self.client.post(self.url, test_email)

        # We shouldn't retry when hitting a 5xx error
        self.assertFalse(retry.called)
        # Test that after the rejected email, the rest still successfully send
        ((sent, fail, optouts), _) = result.call_args
        self.assertEquals(optouts, 0)
        expectedNumFails = int((settings.EMAILS_PER_TASK + 3) / 4.0)
        self.assertEquals(fail, expectedNumFails)
        self.assertEquals(sent, settings.EMAILS_PER_TASK - expectedNumFails)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_disconn_err_retry(self, retry, get_conn):
        """
        Test that celery handles SMTPServerDisconnected by retrying.
        """
        get_conn.return_value.open.side_effect = SMTPServerDisconnected(425, "Disconnecting")
        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        self.client.post(self.url, test_email)

        self.assertTrue(retry.called)
        (_, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertTrue(type(exc) == SMTPServerDisconnected)

    @patch('bulk_email.tasks.get_connection', autospec=True)
    @patch('bulk_email.tasks.send_course_email.retry')
    def test_conn_err_retry(self, retry, get_conn):
        """
        Test that celery handles SMTPConnectError by retrying.
        """
        get_conn.return_value.open.side_effect = SMTPConnectError(424, "Bad Connection")

        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        self.client.post(self.url, test_email)

        self.assertTrue(retry.called)
        (_, kwargs) = retry.call_args
        exc = kwargs['exc']
        self.assertTrue(type(exc) == SMTPConnectError)

    @patch('bulk_email.tasks.create_subtask_result')
    @patch('bulk_email.tasks.send_course_email.retry')
    @patch('bulk_email.tasks.log')
    @patch('bulk_email.tasks.get_connection', Mock(return_value=EmailTestException))
    def test_general_exception(self, mock_log, retry, result):
        """
        Tests the if the error is not SMTP-related, we log and reraise
        """
        test_email = {
            'action': 'Send email',
            'to_option': 'myself',
            'subject': 'test subject for myself',
            'message': 'test message for myself'
        }
        # For some reason (probably the weirdness of testing with celery tasks) assertRaises doesn't work here
        # so we assert on the arguments of log.exception
        self.client.post(self.url, test_email)
        self.assertTrue(mock_log.exception.called)
        ((log_str, _task_id, email_id, to_list), _) = mock_log.exception.call_args
        self.assertIn('caused send_course_email task to fail with uncaught exception.', log_str)
        self.assertEqual(email_id, 1)
        self.assertEqual(to_list, [self.instructor.email])
        self.assertFalse(retry.called)
        # check the results being returned
        self.assertTrue(result.called)
        ((sent, fail, optouts), _) = result.call_args
        self.assertEquals(optouts, 0)
        self.assertEquals(fail, 1)  # just myself
        self.assertEquals(sent, 0)

    @patch('bulk_email.tasks.create_subtask_result')
    @patch('bulk_email.tasks.log')
    def test_nonexist_email(self, mock_log, result):
        """
        Tests retries when the email doesn't exist
        """
        # create an InstructorTask object to pass through
        course_id = self.course.id
        entry = InstructorTask.create(course_id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": -1}
        with self.assertRaises(CourseEmail.DoesNotExist):
            perform_delegate_email_batches(entry.id, course_id, task_input, "action_name")
        ((log_str, email_id), _) = mock_log.warning.call_args
        self.assertTrue(mock_log.warning.called)
        self.assertIn('Failed to get CourseEmail with id', log_str)
        self.assertEqual(email_id, -1)
        self.assertFalse(result.called)

    @patch('bulk_email.tasks.log')
    def test_nonexist_course(self, mock_log):
        """
        Tests exception when the course in the email doesn't exist
        """
        course_id = "I/DONT/EXIST"
        email = CourseEmail(course_id=course_id)
        email.save()
        entry = InstructorTask.create(course_id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": email.id}
        with self.assertRaises(Exception):
            perform_delegate_email_batches(entry.id, course_id, task_input, "action_name")
        ((log_str, _), _) = mock_log.exception.call_args
        self.assertTrue(mock_log.exception.called)
        self.assertIn('get_course_by_id failed:', log_str)

    @patch('bulk_email.tasks.log')
    def test_nonexist_to_option(self, mock_log):
        """
        Tests exception when the to_option in the email doesn't exist
        """
        email = CourseEmail(course_id=self.course.id, to_option="IDONTEXIST")
        email.save()
        entry = InstructorTask.create(self.course.id, "task_type", "task_key", "task_input", self.instructor)
        task_input = {"email_id": email.id}
        with self.assertRaises(Exception):
            perform_delegate_email_batches(entry.id, self.course.id, task_input, "action_name")
        ((log_str, opt_str), _) = mock_log.error.call_args
        self.assertTrue(mock_log.error.called)
        self.assertIn('Unexpected bulk email TO_OPTION found', log_str)
        self.assertEqual("IDONTEXIST", opt_str)
