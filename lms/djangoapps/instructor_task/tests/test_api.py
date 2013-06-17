"""
Test for LMS instructor background task queue management
"""
import logging
import json
from celery.states import SUCCESS, FAILURE, REVOKED, PENDING

from mock import Mock, patch
from uuid import uuid4

from django.utils.datastructures import MultiValueDict
from django.test.testcases import TestCase

from xmodule.modulestore.exceptions import ItemNotFoundError

from courseware.tests.factories import UserFactory

from instructor_task.api import (get_running_instructor_tasks,
                                 get_instructor_task_history,
                                 submit_rescore_problem_for_all_students,
                                 submit_rescore_problem_for_student,
                                 submit_reset_problem_attempts_for_all_students,
                                 submit_delete_problem_state_for_all_students)

from instructor_task.api_helper import (AlreadyRunningError,
                                        encode_problem_and_student_input)
from instructor_task.models import InstructorTask, PROGRESS, QUEUING
from instructor_task.tests.test_base import InstructorTaskTestCase
from instructor_task.tests.factories import InstructorTaskFactory
from instructor_task.views import instructor_task_status, get_task_completion_info


log = logging.getLogger(__name__)


TEST_COURSE_ID = 'edx/1.23x/test_course'
TEST_FAILURE_MESSAGE = 'task failed horribly'
TEST_FAILURE_EXCEPTION = 'RandomCauseError'


class InstructorTaskReportTest(TestCase):
    """
    Tests API and view methods that involve the reporting of status for background tasks.
    """
    def setUp(self):
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")
        self.problem_url = InstructorTaskReportTest.problem_location("test_urlname")

    @staticmethod
    def problem_location(problem_url_name):
        """
        Create an internal location for a test problem.
        """
        return "i4x://{org}/{number}/problem/{problem_url_name}".format(org='edx',
                                                                        number='1.23x',
                                                                        problem_url_name=problem_url_name)

    def _create_entry(self, task_state=QUEUING, task_output=None, student=None):
        """Creates a InstructorTask entry for testing."""
        task_id = str(uuid4())
        progress_json = json.dumps(task_output) if task_output is not None else None
        task_input, task_key = encode_problem_and_student_input(self.problem_url, student)

        instructor_task = InstructorTaskFactory.create(course_id=TEST_COURSE_ID,
                                                       requester=self.instructor,
                                                       task_input=json.dumps(task_input),
                                                       task_key=task_key,
                                                       task_id=task_id,
                                                       task_state=task_state,
                                                       task_output=progress_json)
        return instructor_task

    def _create_failure_entry(self):
        """Creates a InstructorTask entry representing a failed task."""
        # view task entry for task failure
        progress = {'message': TEST_FAILURE_MESSAGE,
                    'exception': TEST_FAILURE_EXCEPTION,
                    }
        return self._create_entry(task_state=FAILURE, task_output=progress)

    def _create_success_entry(self, student=None):
        """Creates a InstructorTask entry representing a successful task."""
        return self._create_progress_entry(student, task_state=SUCCESS)

    def _create_progress_entry(self, student=None, task_state=PROGRESS):
        """Creates a InstructorTask entry representing a task in progress."""
        progress = {'attempted': 3,
                    'updated': 2,
                    'total': 5,
                    'action_name': 'rescored',
                    }
        return self._create_entry(task_state=task_state, task_output=progress, student=student)

    def test_get_running_instructor_tasks(self):
        # when fetching running tasks, we get all running tasks, and only running tasks
        for _ in range(1, 5):
            self._create_failure_entry()
            self._create_success_entry()
        progress_task_ids = [self._create_progress_entry().task_id for _ in range(1, 5)]
        task_ids = [instructor_task.task_id for instructor_task in get_running_instructor_tasks(TEST_COURSE_ID)]
        self.assertEquals(set(task_ids), set(progress_task_ids))

    def test_get_instructor_task_history(self):
        # when fetching historical tasks, we get all tasks, including running tasks
        expected_ids = []
        for _ in range(1, 5):
            expected_ids.append(self._create_failure_entry().task_id)
            expected_ids.append(self._create_success_entry().task_id)
            expected_ids.append(self._create_progress_entry().task_id)
        task_ids = [instructor_task.task_id for instructor_task
                    in get_instructor_task_history(TEST_COURSE_ID, self.problem_url)]
        self.assertEquals(set(task_ids), set(expected_ids))

    def _get_instructor_task_status(self, task_id):
        """Returns status corresponding to task_id via api method."""
        request = Mock()
        request.REQUEST = {'task_id': task_id}
        return instructor_task_status(request)

    def test_instructor_task_status(self):
        instructor_task = self._create_failure_entry()
        task_id = instructor_task.task_id
        request = Mock()
        request.REQUEST = {'task_id': task_id}
        response = instructor_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)

    def test_instructor_task_status_list(self):
        # Fetch status for existing tasks by arg list, as if called from ajax.
        # Note that ajax does something funny with the marshalling of
        # list data, so the key value has "[]" appended to it.
        task_ids = [(self._create_failure_entry()).task_id for _ in range(1, 5)]
        request = Mock()
        request.REQUEST = MultiValueDict({'task_ids[]': task_ids})
        response = instructor_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(len(output), len(task_ids))
        for task_id in task_ids:
            self.assertEquals(output[task_id]['task_id'], task_id)

    def test_get_status_from_failure(self):
        # get status for a task that has already failed
        instructor_task = self._create_failure_entry()
        task_id = instructor_task.task_id
        response = self._get_instructor_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['message'], TEST_FAILURE_MESSAGE)
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], FAILURE)
        self.assertFalse(output['in_progress'])
        expected_progress = {'exception': TEST_FAILURE_EXCEPTION,
                             'message': TEST_FAILURE_MESSAGE}
        self.assertEquals(output['task_progress'], expected_progress)

    def test_get_status_from_success(self):
        # get status for a task that has already succeeded
        instructor_task = self._create_success_entry()
        task_id = instructor_task.task_id
        response = self._get_instructor_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['message'], "Problem rescored for 2 of 3 students (out of 5)")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])
        expected_progress = {'attempted': 3,
                             'updated': 2,
                             'total': 5,
                             'action_name': 'rescored'}
        self.assertEquals(output['task_progress'], expected_progress)

    def _test_get_status_from_result(self, task_id, mock_result):
        """
        Provides mock result to caller of instructor_task_status, and returns resulting output.
        """
        with patch('celery.result.AsyncResult.__new__') as mock_result_ctor:
            mock_result_ctor.return_value = mock_result
            response = self._get_instructor_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)
        return output

    def test_get_status_to_pending(self):
        # get status for a task that hasn't begun to run yet
        instructor_task = self._create_entry()
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = PENDING
        output = self._test_get_status_from_result(task_id, mock_result)
        for key in ['message', 'succeeded', 'task_progress']:
            self.assertTrue(key not in output)
        self.assertEquals(output['task_state'], 'PENDING')
        self.assertTrue(output['in_progress'])

    def test_update_progress_to_progress(self):
        # view task entry for task in progress
        instructor_task = self._create_progress_entry()
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = PROGRESS
        mock_result.result = {'attempted': 5,
                              'updated': 4,
                              'total': 10,
                              'action_name': 'rescored'}
        output = self._test_get_status_from_result(task_id, mock_result)
        self.assertEquals(output['message'], "Progress: rescored 4 of 5 so far (out of 10)")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_state'], PROGRESS)
        self.assertTrue(output['in_progress'])
        self.assertEquals(output['task_progress'], mock_result.result)

    def test_update_progress_to_failure(self):
        # view task entry for task in progress that later fails
        instructor_task = self._create_progress_entry()
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = FAILURE
        mock_result.result = NotImplementedError("This task later failed.")
        mock_result.traceback = "random traceback"
        output = self._test_get_status_from_result(task_id, mock_result)
        self.assertEquals(output['message'], "This task later failed.")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_state'], FAILURE)
        self.assertFalse(output['in_progress'])
        expected_progress = {'exception': 'NotImplementedError',
                             'message': "This task later failed.",
                             'traceback': "random traceback"}
        self.assertEquals(output['task_progress'], expected_progress)

    def test_update_progress_to_revoked(self):
        # view task entry for task in progress that later fails
        instructor_task = self._create_progress_entry()
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = REVOKED
        output = self._test_get_status_from_result(task_id, mock_result)
        self.assertEquals(output['message'], "Task revoked before running")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_state'], REVOKED)
        self.assertFalse(output['in_progress'])
        expected_progress = {'message': "Task revoked before running"}
        self.assertEquals(output['task_progress'], expected_progress)

    def _get_output_for_task_success(self, attempted, updated, total, student=None):
        """returns the task_id and the result returned by instructor_task_status()."""
        # view task entry for task in progress
        instructor_task = self._create_progress_entry(student)
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = SUCCESS
        mock_result.result = {'attempted': attempted,
                              'updated': updated,
                              'total': total,
                              'action_name': 'rescored'}
        output = self._test_get_status_from_result(task_id, mock_result)
        return output

    def test_update_progress_to_success(self):
        output = self._get_output_for_task_success(10, 8, 10)
        self.assertEquals(output['message'], "Problem rescored for 8 of 10 students")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])
        expected_progress = {'attempted': 10,
                             'updated': 8,
                             'total': 10,
                             'action_name': 'rescored'}
        self.assertEquals(output['task_progress'], expected_progress)

    def test_success_messages(self):
        output = self._get_output_for_task_success(0, 0, 10)
        self.assertEqual(output['message'], "Unable to find any students with submissions to be rescored (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(10, 0, 10)
        self.assertEqual(output['message'], "Problem failed to be rescored for any of 10 students")
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(10, 8, 10)
        self.assertEqual(output['message'], "Problem rescored for 8 of 10 students")
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(9, 8, 10)
        self.assertEqual(output['message'], "Problem rescored for 8 of 9 students (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(10, 10, 10)
        self.assertEqual(output['message'], "Problem successfully rescored for 10 students")
        self.assertTrue(output['succeeded'])

        output = self._get_output_for_task_success(0, 0, 1, student=self.student)
        self.assertTrue("Unable to find submission to be rescored for student" in output['message'])
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(1, 0, 1, student=self.student)
        self.assertTrue("Problem failed to be rescored for student" in output['message'])
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(1, 1, 1, student=self.student)
        self.assertTrue("Problem successfully rescored for student" in output['message'])
        self.assertTrue(output['succeeded'])

    def test_get_info_for_queuing_task(self):
        # get status for a task that is still running:
        instructor_task = self._create_entry()
        succeeded, message = get_task_completion_info(instructor_task)
        self.assertFalse(succeeded)
        self.assertEquals(message, "No status information available")

    def test_get_info_for_missing_output(self):
        # check for missing task_output
        instructor_task = self._create_success_entry()
        instructor_task.task_output = None
        succeeded, message = get_task_completion_info(instructor_task)
        self.assertFalse(succeeded)
        self.assertEquals(message, "No status information available")

    def test_get_info_for_broken_output(self):
        # check for non-JSON task_output
        instructor_task = self._create_success_entry()
        instructor_task.task_output = "{ bad"
        succeeded, message = get_task_completion_info(instructor_task)
        self.assertFalse(succeeded)
        self.assertEquals(message, "No parsable status information available")

    def test_get_info_for_empty_output(self):
        # check for JSON task_output with missing keys
        instructor_task = self._create_success_entry()
        instructor_task.task_output = "{}"
        succeeded, message = get_task_completion_info(instructor_task)
        self.assertFalse(succeeded)
        self.assertEquals(message, "No progress status information available")

    def test_get_info_for_broken_input(self):
        # check for non-JSON task_input, but then just ignore it
        instructor_task = self._create_success_entry()
        instructor_task.task_input = "{ bad"
        succeeded, message = get_task_completion_info(instructor_task)
        self.assertFalse(succeeded)
        self.assertEquals(message, "Problem rescored for 2 of 3 students (out of 5)")


class InstructorTaskSubmitTest(InstructorTaskTestCase):
    """Tests API methods that involve the submission of background tasks."""

    def setUp(self):
        self.initialize_course()
        self.student = UserFactory.create(username="student", email="student@edx.org")
        self.instructor = UserFactory.create(username="instructor", email="instructor@edx.org")

    def test_submit_nonexistent_modules(self):
        # confirm that a rescore of a non-existent module returns an exception
        # (Note that it is easier to test a non-rescorable module in test_tasks,
        # where we are creating real modules.
        problem_url = InstructorTaskTestCase.problem_location("NonexistentProblem")
        course_id = self.course.id
        request = None
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(ItemNotFoundError):
            submit_rescore_problem_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_reset_problem_attempts_for_all_students(request, course_id, problem_url)
        with self.assertRaises(ItemNotFoundError):
            submit_delete_problem_state_for_all_students(request, course_id, problem_url)

    def test_submit_nonrescorable_modules(self):
        # confirm that a rescore of an existent but unscorable module returns an exception
        # (Note that it is easier to test a non-rescorable module in test_tasks,
        # where we are creating real modules.)
        problem_url = self.problem_section.location.url()
        course_id = self.course.id
        request = None
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_student(request, course_id, problem_url, self.student)
        with self.assertRaises(NotImplementedError):
            submit_rescore_problem_for_all_students(request, course_id, problem_url)

    def _test_submit_with_long_url(self, task_class, student=None):
        problem_url_name = 'x' * 255
        self.define_option_problem(problem_url_name)
        location = InstructorTaskTestCase.problem_location(problem_url_name)
        with self.assertRaises(ValueError):
            if student is not None:
                task_class(self.create_task_request(self.instructor), self.course.id, location, student)
            else:
                task_class(self.create_task_request(self.instructor), self.course.id, location)

    def test_submit_rescore_all_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_all_students)

    def test_submit_rescore_student_with_long_url(self):
        self._test_submit_with_long_url(submit_rescore_problem_for_student, self.student)

    def test_submit_reset_all_with_long_url(self):
        self._test_submit_with_long_url(submit_reset_problem_attempts_for_all_students)

    def test_submit_delete_all_with_long_url(self):
        self._test_submit_with_long_url(submit_delete_problem_state_for_all_students)

    def _test_submit_task(self, task_class, student=None):
        problem_url_name = 'H1P1'
        self.define_option_problem(problem_url_name)
        location = InstructorTaskTestCase.problem_location(problem_url_name)
        if student is not None:
            instructor_task = task_class(self.create_task_request(self.instructor),
                                         self.course.id, location, student)
        else:
            instructor_task = task_class(self.create_task_request(self.instructor),
                                         self.course.id, location)

        # test resubmitting, by updating the existing record:
        instructor_task = InstructorTask.objects.get(id=instructor_task.id)
        instructor_task.task_state = PROGRESS
        instructor_task.save()

        with self.assertRaises(AlreadyRunningError):
            if student is not None:
                task_class(self.create_task_request(self.instructor), self.course.id, location, student)
            else:
                task_class(self.create_task_request(self.instructor), self.course.id, location)

    def test_submit_rescore_all(self):
        self._test_submit_task(submit_rescore_problem_for_all_students)

    def test_submit_rescore_student(self):
        self._test_submit_task(submit_rescore_problem_for_student, self.student)

    def test_submit_reset_all(self):
        self._test_submit_task(submit_reset_problem_attempts_for_all_students)

    def test_submit_delete_all(self):
        self._test_submit_task(submit_delete_problem_state_for_all_students)

