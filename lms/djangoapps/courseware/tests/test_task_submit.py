"""
Test for LMS courseware background task queue management
"""
import logging
import json
from celery.states import SUCCESS, FAILURE, REVOKED

from mock import Mock, patch
from uuid import uuid4

from django.utils.datastructures import MultiValueDict
from django.test.testcases import TestCase

from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.tests.factories import UserFactory, CourseTaskFactory
from courseware.tasks import PROGRESS
from courseware.task_submit import (QUEUING,
                                    get_running_course_tasks,
                                    course_task_status,
                                    _encode_problem_and_student_input,
                                    AlreadyRunningError,
                                    submit_rescore_problem_for_all_students,
                                    submit_rescore_problem_for_student,
                                    submit_reset_problem_attempts_for_all_students,
                                    submit_delete_problem_state_for_all_students)


log = logging.getLogger(__name__)


TEST_COURSE_ID = 'edx/1.23x/test_course'
TEST_FAILURE_MESSAGE = 'task failed horribly'


class TaskSubmitTestCase(TestCase):
    """
    Check that background tasks are properly queued and report status.
    """
    def setUp(self):
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")
        self.problem_url = TaskSubmitTestCase.problem_location("test_urlname")

    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        return "i4x://{org}/{number}/problem/{problem_url_name}".format(org='edx',
                                                                        number='1.23x',
                                                                        problem_url_name=problem_url_name)

    def _create_entry(self, task_state=QUEUING, task_output=None, student=None):
        """Creates a CourseTask entry for testing."""
        task_id = str(uuid4())
        progress_json = json.dumps(task_output)
        task_input, task_key = _encode_problem_and_student_input(self.problem_url, student)

        course_task = CourseTaskFactory.create(course_id=TEST_COURSE_ID,
                                               requester=self.instructor,
                                               task_input=json.dumps(task_input),
                                               task_key=task_key,
                                               task_id=task_id,
                                               task_state=task_state,
                                               task_output=progress_json)
        return course_task

    def _create_failure_entry(self):
        """Creates a CourseTask entry representing a failed task."""
        # view task entry for task failure
        progress = {'message': TEST_FAILURE_MESSAGE,
                    'exception': 'RandomCauseError',
                    }
        return self._create_entry(task_state=FAILURE, task_output=progress)

    def _create_success_entry(self, student=None):
        """Creates a CourseTask entry representing a successful task."""
        return self._create_progress_entry(student, task_state=SUCCESS)

    def _create_progress_entry(self, student=None, task_state=PROGRESS):
        """Creates a CourseTask entry representing a task in progress."""
        progress = {'attempted': 3,
                    'updated': 2,
                    'total': 10,
                    'action_name': 'rescored',
                    'message': 'some random string that should summarize the other info',
                    }
        return self._create_entry(task_state=task_state, task_output=progress, student=student)

    def test_fetch_running_tasks(self):
        # when fetching running tasks, we get all running tasks, and only running tasks
        for _ in range(1, 5):
            self._create_failure_entry()
            self._create_success_entry()
        progress_task_ids = [self._create_progress_entry().task_id for _ in range(1, 5)]
        task_ids = [course_task.task_id for course_task in get_running_course_tasks(TEST_COURSE_ID)]
        self.assertEquals(set(task_ids), set(progress_task_ids))

    def _get_course_task_status(self, task_id):
        request = Mock()
        request.REQUEST = {'task_id': task_id}
        return course_task_status(request)

    def test_course_task_status(self):
        course_task = self._create_failure_entry()
        task_id = course_task.task_id
        request = Mock()
        request.REQUEST = {'task_id': task_id}
        response = course_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)

    def test_course_task_status_list(self):
        # Fetch status for existing tasks by arg list, as if called from ajax.
        # Note that ajax does something funny with the marshalling of
        # list data, so the key value has "[]" appended to it.
        task_ids = [(self._create_failure_entry()).task_id for _ in range(1, 5)]
        request = Mock()
        request.REQUEST = MultiValueDict({'task_ids[]': task_ids})
        response = course_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(len(output), len(task_ids))
        for task_id in task_ids:
            self.assertEquals(output[task_id]['task_id'], task_id)

    def test_get_status_from_failure(self):
        course_task = self._create_failure_entry()
        task_id = course_task.task_id
        response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], FAILURE)
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], TEST_FAILURE_MESSAGE)

    def test_get_status_from_success(self):
        course_task = self._create_success_entry()
        task_id = course_task.task_id
        response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])

    def test_update_progress_to_progress(self):
        # view task entry for task in progress
        course_task = self._create_progress_entry()
        task_id = course_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = PROGRESS
        mock_result.result = {'attempted': 5,
                              'updated': 4,
                              'total': 10,
                              'action_name': 'rescored'}
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], PROGRESS)
        self.assertTrue(output['in_progress'])
        # self.assertEquals(output['message'], )

    def test_update_progress_to_failure(self):
        # view task entry for task in progress that later fails
        course_task = self._create_progress_entry()
        task_id = course_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = FAILURE
        mock_result.result = NotImplementedError("This task later failed.")
        mock_result.traceback = "random traceback"
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], FAILURE)
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], "This task later failed.")

    def test_update_progress_to_revoked(self):
        # view task entry for task in progress that later fails
        course_task = self._create_progress_entry()
        task_id = course_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = REVOKED
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], REVOKED)
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], "Task revoked before running")

    def _get_output_for_task_success(self, attempted, updated, total, student=None):
        """returns the task_id and the result returned by course_task_status()."""
        # view task entry for task in progress
        course_task = self._create_progress_entry(student)
        task_id = course_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = SUCCESS
        mock_result.result = {'attempted': attempted,
                              'updated': updated,
                              'total': total,
                              'action_name': 'rescored'}
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = self._get_course_task_status(task_id)
        output = json.loads(response.content)
        return task_id, output

    def test_update_progress_to_success(self):
        task_id, output = self._get_output_for_task_success(10, 8, 10)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])

    def teBROKENst_success_messages(self):
        _, output = self._get_output_for_task_success(0, 0, 10)
        self.assertTrue("Unable to find any students with submissions to be rescored" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 0, 10)
        self.assertTrue("Problem failed to be rescored for any of 10 students" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 8, 10)
        self.assertTrue("Problem rescored for 8 of 10 students" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 10, 10)
        self.assertTrue("Problem successfully rescored for 10 students" in output['message'])
        self.assertTrue(output['succeeded'])

        _, output = self._get_output_for_task_success(0, 0, 1, student=self.student)
        self.assertTrue("Unable to find submission to be rescored for student" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(1, 0, 1, student=self.student)
        self.assertTrue("Problem failed to be rescored for student" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(1, 1, 1, student=self.student)
        self.assertTrue("Problem successfully rescored for student" in output['message'])
        self.assertTrue(output['succeeded'])

    def test_submit_nonexistent_modules(self):
        # confirm that a rescore of a non-existent module returns an exception
        # (Note that it is easier to test a non-rescorable module in test_tasks,
        # where we are creating real modules.
        problem_url = self.problem_url
        course_id = "something else"
        request = None
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_reset_problem_attempts_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_delete_problem_state_for_all_students(request, course_id, problem_url)

    def test_submit_when_running(self):
        # get exception when trying to submit a task that is already running
        course_task = self._create_progress_entry()
        problem_url = json.loads(course_task.task_input).get('problem_url')
        course_id = course_task.course_id
        # requester doesn't have to be the same when determining if a task is already running
        request = Mock()
        request.user = self.student
        with self.assertRaises(AlreadyRunningError):
            # just skip making the argument check, so we don't have to fake it deeper down
            with patch('courseware.task_submit._check_arguments_for_rescoring'):
                submit_rescore_problem_for_all_students(request, course_id, problem_url)
