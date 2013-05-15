"""
Test for LMS courseware background task queue management
"""
import logging
import json
from mock import Mock, patch
from uuid import uuid4

from django.utils.datastructures import MultiValueDict
from django.test.testcases import TestCase

from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.tests.factories import UserFactory, CourseTaskLogFactory
from courseware.task_queue import (get_running_course_tasks, 
                                   course_task_log_status,
                                   AlreadyRunningError,
                                   submit_regrade_problem_for_all_students, 
                                   submit_regrade_problem_for_student,
                                   submit_reset_problem_attempts_for_all_students,
                                   submit_delete_problem_state_for_all_students)


log = logging.getLogger("mitx." + __name__)


TEST_FAILURE_MESSAGE = 'task failed horribly'


class TaskQueueTestCase(TestCase):
    """
    Check that background tasks are properly queued and report status.
    """
    student = None
    instructor = None
    problem_url = None

    def setUp(self):
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="student@edx.org")
        self.problem_url = TaskQueueTestCase.problem_location("test_urlname")

    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        if "i4x:" in problem_url_name:
            return problem_url_name
        else:
            return "i4x://{org}/{number}/problem/{problem_url_name}".format(org='edx',
                                                                            number='1.23x',
                                                                            problem_url_name=problem_url_name)

    def _create_entry(self, task_state="QUEUED", task_progress=None, student=None):
        task_id = str(uuid4())
        progress_json = json.dumps(task_progress)
        course_task_log = CourseTaskLogFactory.create(student=student,
                                                      requester=self.instructor,
                                                      task_args=self.problem_url,
                                                      task_id=task_id,
                                                      task_state=task_state,
                                                      task_progress=progress_json)
        return course_task_log

    def _create_failure_entry(self):
        # view task entry for task failure
        progress = {'message': TEST_FAILURE_MESSAGE,
                    'exception': 'RandomCauseError',
                    }
        return self._create_entry(task_state="FAILURE", task_progress=progress)

    def _create_success_entry(self, student=None):
        return self._create_progress_entry(student=None, task_state="SUCCESS")

    def _create_progress_entry(self, student=None, task_state="PROGRESS"):
        # view task entry for task failure
        progress = {'attempted': 3,
                    'updated': 2,
                    'total': 10,
                    'action_name': 'regraded',
                    'message': 'some random string that should summarize the other info',
                    }
        return self._create_entry(task_state=task_state, task_progress=progress, student=student)

    def test_fetch_running_tasks(self):
        # when fetching running tasks, we get all running tasks, and only running tasks
        failure_task_ids = [(self._create_failure_entry()).task_id for _ in range(1, 4)]
        entry = self._create_failure_entry()
        failure_task_ids.append(entry.task_id)
        course_id = entry.course_id  # get course_id used by the factory
        success_task_ids = [(self._create_success_entry()).task_id for _ in range(1, 5)]
        progress_task_ids = [(self._create_progress_entry()).task_id for _ in range(1, 5)]
        task_ids = [course_task_log.task_id for course_task_log in get_running_course_tasks(course_id)]
        self.assertEquals(len(task_ids), len(progress_task_ids))
        for task_id in task_ids:
            self.assertTrue(task_id in progress_task_ids)
            self.assertFalse(task_id in success_task_ids)
            self.assertFalse(task_id in failure_task_ids)

    def test_course_task_log_status_by_post(self):
        # fetch status for existing tasks: by arg is tested elsewhere,
        # so test by POST arg
        course_task_log = self._create_failure_entry()
        task_id = course_task_log.task_id
        request = Mock()
        request.POST = {}
        request.POST['task_id'] = task_id
        response = course_task_log_status(request)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)

    def test_course_task_log_status_list_by_post(self):
        # Fetch status for existing tasks: by arg is tested elsewhere,
        # so test here by POST arg list, as if called from ajax.
        # Note that ajax does something funny with the marshalling of
        # list data, so the key value has "[]" appended to it.
        task_ids = [(self._create_failure_entry()).task_id for _ in range(1, 5)]
        request = Mock()
        request.POST = MultiValueDict({'task_ids[]': task_ids})
        response = course_task_log_status(request)
        output = json.loads(response.content)
        for task_id in task_ids:
            self.assertEquals(output[task_id]['task_id'], task_id)

    def test_initial_failure(self):
        course_task_log = self._create_failure_entry()
        task_id = course_task_log.task_id
        response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "FAILURE")
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], TEST_FAILURE_MESSAGE)

    def test_initial_success(self):
        course_task_log = self._create_success_entry()
        task_id = course_task_log.task_id
        response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "SUCCESS")
        self.assertFalse(output['in_progress'])

    def test_update_progress_to_progress(self):
        # view task entry for task in progress
        course_task_log = self._create_progress_entry()
        task_id = course_task_log.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = "PROGRESS"
        mock_result.result = {'attempted': 5,
                              'updated': 4,
                              'total': 10,
                              'action_name': 'regraded'}
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "PROGRESS")
        self.assertTrue(output['in_progress'])
        # self.assertEquals(output['message'], )

    def test_update_progress_to_failure(self):
        # view task entry for task in progress that later fails
        course_task_log = self._create_progress_entry()
        task_id = course_task_log.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = "FAILURE"
        mock_result.result = NotImplementedError("This task later failed.")
        mock_result.traceback = "random traceback"
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "FAILURE")
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], "This task later failed.")

    def test_update_progress_to_revoked(self):
        # view task entry for task in progress that later fails
        course_task_log = self._create_progress_entry()
        task_id = course_task_log.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = "REVOKED"
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "REVOKED")
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['message'], "Task revoked before running")

    def _get_output_for_task_success(self, attempted, updated, total, student=None):
        # view task entry for task in progress
        course_task_log = self._create_progress_entry(student)
        task_id = course_task_log.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = "SUCCESS"
        mock_result.result = {'attempted': attempted,
                              'updated': updated,
                              'total': total,
                              'action_name': 'regraded'}
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = course_task_log_status(Mock(), task_id=task_id)
        output = json.loads(response.content)
        return task_id, output

    def test_update_progress_to_success(self):
        task_id, output = self._get_output_for_task_success(10, 8, 10)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], "SUCCESS")
        self.assertFalse(output['in_progress'])

    def test_success_messages(self):
        _, output = self._get_output_for_task_success(0, 0, 10)
        self.assertTrue("Unable to find any students with submissions to be regraded" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 0, 10)
        self.assertTrue("Problem failed to be regraded for any of 10 students " in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 8, 10)
        self.assertTrue("Problem regraded for 8 of 10 students" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(10, 10, 10)
        self.assertTrue("Problem successfully regraded for 10 students" in output['message'])
        self.assertTrue(output['succeeded'])

        _, output = self._get_output_for_task_success(0, 0, 1, student=self.student)
        self.assertTrue("Unable to find submission to be regraded for student" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(1, 0, 1, student=self.student)
        self.assertTrue("Problem failed to be regraded for student" in output['message'])
        self.assertFalse(output['succeeded'])

        _, output = self._get_output_for_task_success(1, 1, 1, student=self.student)
        self.assertTrue("Problem successfully regraded for student" in output['message'])
        self.assertTrue(output['succeeded'])

    def test_submit_nonexistent_modules(self):
        # confirm that a regrade of a non-existent module returns an exception
        # (Note that it is easier to test a non-regradable module in test_tasks,
        # where we are creating real modules.
        problem_url = self.problem_url
        course_id = "something else"
        request = None
        with self.assertRaises(ItemNotFoundError):
            submit_regrade_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(ItemNotFoundError):
            submit_regrade_problem_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_reset_problem_attempts_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_delete_problem_state_for_all_students(request, course_id, problem_url)

    def test_submit_when_running(self):
        # get exception when trying to submit a task that is already running
        course_task_log = self._create_progress_entry()
        problem_url = course_task_log.task_args
        course_id = course_task_log.course_id
        # requester doesn't have to be the same when determining if a task is already running
        request = Mock()
        request.user = self.student
        with self.assertRaises(AlreadyRunningError):
            # just skip making the argument check, so we don't have to fake it deeper down
            with patch('courseware.task_queue._check_arguments_for_regrading'):
                submit_regrade_problem_for_all_students(request, course_id, problem_url)
