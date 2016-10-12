
"""
Test for LMS instructor background task views.
"""
import json
from celery.states import SUCCESS, FAILURE, REVOKED, PENDING

from mock import Mock, patch

from django.http import QueryDict

from instructor_task.models import PROGRESS
from instructor_task.tests.test_base import (InstructorTaskTestCase,
                                             TEST_FAILURE_MESSAGE,
                                             TEST_FAILURE_EXCEPTION)
from instructor_task.views import instructor_task_status, get_task_completion_info


class InstructorTaskReportTest(InstructorTaskTestCase):
    """
    Tests view methods that involve the reporting of status for background tasks.
    """

    def _get_instructor_task_status(self, task_id):
        """Returns status corresponding to task_id via api method."""
        request = Mock()
        request.GET = request.POST = {'task_id': task_id}
        return instructor_task_status(request)

    def test_instructor_task_status(self):
        instructor_task = self._create_failure_entry()
        task_id = instructor_task.task_id
        request = Mock()
        request.GET = request.POST = {'task_id': task_id}
        response = instructor_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(output['task_id'], task_id)

    def test_missing_instructor_task_status(self):
        task_id = "missing_id"
        request = Mock()
        request.GET = request.POST = {'task_id': task_id}
        response = instructor_task_status(request)
        output = json.loads(response.content)
        self.assertEquals(output, {})

    def test_instructor_task_status_list(self):
        # Fetch status for existing tasks by arg list, as if called from ajax.
        # Note that ajax does something funny with the marshalling of
        # list data, so the key value has "[]" appended to it.
        task_ids = [(self._create_failure_entry()).task_id for _ in range(1, 5)]
        request = Mock()
        task_ids_query_dict = QueryDict(mutable=True)
        task_ids_query_dict.update({'task_ids[]': task_ids})
        request.GET = request.POST = task_ids_query_dict
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
        expected_progress = {
            'exception': TEST_FAILURE_EXCEPTION,
            'message': TEST_FAILURE_MESSAGE,
        }
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
        expected_progress = {
            'attempted': 3,
            'succeeded': 2,
            'total': 5,
            'action_name': 'rescored',
        }
        self.assertEquals(output['task_progress'], expected_progress)

    def test_get_status_from_legacy_success(self):
        # get status for a task that had already succeeded, back at a time
        # when 'updated' was used instead of the preferred 'succeeded'.
        legacy_progress = {
            'attempted': 3,
            'updated': 2,
            'total': 5,
            'action_name': 'rescored',
        }
        instructor_task = self._create_entry(task_state=SUCCESS, task_output=legacy_progress)
        task_id = instructor_task.task_id
        response = self._get_instructor_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['message'], "Problem rescored for 2 of 3 students (out of 5)")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])
        self.assertEquals(output['task_progress'], legacy_progress)

    def _create_email_subtask_entry(self, total=5, attempted=3, succeeded=2, skipped=0, task_state=PROGRESS):
        """Create an InstructorTask with subtask defined and email argument."""
        progress = {'attempted': attempted,
                    'succeeded': succeeded,
                    'skipped': skipped,
                    'total': total,
                    'action_name': 'emailed',
                    }
        instructor_task = self._create_entry(task_state=task_state, task_output=progress)
        instructor_task.subtasks = {}
        instructor_task.task_input = json.dumps({'email_id': 134})
        instructor_task.save()
        return instructor_task

    def test_get_status_from_subtasks(self):
        # get status for a task that is in progress, with updates
        # from subtasks.
        instructor_task = self._create_email_subtask_entry(skipped=1)
        task_id = instructor_task.task_id
        response = self._get_instructor_task_status(task_id)
        output = json.loads(response.content)
        self.assertEquals(output['message'], "Progress: emailed 2 of 3 so far (skipping 1) (out of 5)")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_id'], task_id)
        self.assertEquals(output['task_state'], PROGRESS)
        self.assertTrue(output['in_progress'])
        expected_progress = {
            'attempted': 3,
            'succeeded': 2,
            'skipped': 1,
            'total': 5,
            'action_name': 'emailed',
        }
        self.assertEquals(output['task_progress'], expected_progress)

    def _test_get_status_from_result(self, task_id, mock_result=None):
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
            self.assertNotIn(key, output)
        self.assertEquals(output['task_state'], 'PENDING')
        self.assertTrue(output['in_progress'])

    def test_update_progress_to_progress(self):
        # view task entry for task in progress
        instructor_task = self._create_progress_entry()
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = PROGRESS
        mock_result.result = {
            'attempted': 5,
            'succeeded': 4,
            'total': 10,
            'action_name': 'rescored',
        }
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
        expected_progress = {
            'exception': 'NotImplementedError',
            'message': "This task later failed.",
            'traceback': "random traceback",
        }
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

    def _get_output_for_task_success(self, attempted, succeeded, total, student=None):
        """returns the task_id and the result returned by instructor_task_status()."""
        # view task entry for task in progress
        instructor_task = self._create_progress_entry(student)
        task_id = instructor_task.task_id
        mock_result = Mock()
        mock_result.task_id = task_id
        mock_result.state = SUCCESS
        mock_result.result = {
            'attempted': attempted,
            'succeeded': succeeded,
            'total': total,
            'action_name': 'rescored',
        }
        output = self._test_get_status_from_result(task_id, mock_result)
        return output

    def _get_email_output_for_task_success(self, attempted, succeeded, total, skipped=0):
        """returns the result returned by instructor_task_status()."""
        instructor_task = self._create_email_subtask_entry(
            total=total,
            attempted=attempted,
            succeeded=succeeded,
            skipped=skipped,
            task_state=SUCCESS,
        )
        return self._test_get_status_from_result(instructor_task.task_id)

    def test_update_progress_to_success(self):
        output = self._get_output_for_task_success(10, 8, 10)
        self.assertEquals(output['message'], "Problem rescored for 8 of 10 students")
        self.assertEquals(output['succeeded'], False)
        self.assertEquals(output['task_state'], SUCCESS)
        self.assertFalse(output['in_progress'])
        expected_progress = {
            'attempted': 10,
            'succeeded': 8,
            'total': 10,
            'action_name': 'rescored',
        }
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
        self.assertIn("Unable to find submission to be rescored for student", output['message'])
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(1, 0, 1, student=self.student)
        self.assertIn("Problem failed to be rescored for student", output['message'])
        self.assertFalse(output['succeeded'])

        output = self._get_output_for_task_success(1, 1, 1, student=self.student)
        self.assertIn("Problem successfully rescored for student", output['message'])
        self.assertTrue(output['succeeded'])

    def test_email_success_messages(self):
        output = self._get_email_output_for_task_success(0, 0, 10)
        self.assertEqual(output['message'], "Unable to find any recipients to be emailed (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 0, 10)
        self.assertEqual(output['message'], "Message failed to be emailed for any of 10 recipients ")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 8, 10)
        self.assertEqual(output['message'], "Message emailed for 8 of 10 recipients")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(9, 8, 10)
        self.assertEqual(output['message'], "Message emailed for 8 of 9 recipients (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 10, 10)
        self.assertEqual(output['message'], "Message successfully emailed for 10 recipients")
        self.assertTrue(output['succeeded'])

        output = self._get_email_output_for_task_success(0, 0, 10, skipped=3)
        self.assertEqual(output['message'], "Unable to find any recipients to be emailed (skipping 3) (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 0, 10, skipped=3)
        self.assertEqual(output['message'], "Message failed to be emailed for any of 10 recipients  (skipping 3)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 8, 10, skipped=3)
        self.assertEqual(output['message'], "Message emailed for 8 of 10 recipients (skipping 3)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(9, 8, 10, skipped=3)
        self.assertEqual(output['message'], "Message emailed for 8 of 9 recipients (skipping 3) (out of 10)")
        self.assertFalse(output['succeeded'])

        output = self._get_email_output_for_task_success(10, 10, 10, skipped=3)
        self.assertEqual(output['message'], "Message successfully emailed for 10 recipients (skipping 3)")
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
        self.assertEquals(message, "Status: rescored 2 of 3 (out of 5)")
