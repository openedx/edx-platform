"""
Unit tests for stub ORA implementation.
"""

import unittest
import requests
import json
from ..ora import StubOraService, StudentState


class StubOraServiceTest(unittest.TestCase):

    def setUp(self):
        """
        Start the stub server.
        """
        super(StubOraServiceTest, self).setUp()
        self.server = StubOraService()
        self.addCleanup(self.server.shutdown)

    def test_calibration(self):

        # Ensure that we use the same student ID throughout
        student_id = '1234'

        # Initially, student should not be calibrated
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 0,
            'calibrated': False
        })

        # Retrieve a calibration essay
        response = requests.get(
            self._peer_url('show_calibration_essay'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'student_response': self.server.DUMMY_DATA['student_response'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

        # Grade the calibration essay
        response = requests.post(
            self._peer_url('save_calibration_essay'),
            data={
                'student_id': student_id,
                'location': 'test location',
                'calibration_essay_id': 1,
                'score': 2,
                'submission_key': 'key',
                'feedback': 'Good job!'
            }
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'message': self.server.DUMMY_DATA['message'],
            'actual_score': self.server.DUMMY_DATA['actual_score'],
            'actual_rubric': self.server.DUMMY_DATA['actual_rubric'],
            'actual_feedback': self.server.DUMMY_DATA['actual_feedback']
        })

        # Now the student should be calibrated
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': student_id, 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 1,
            'calibrated': True
        })

        # But a student with a different ID should NOT be calibrated.
        response = requests.get(
            self._peer_url('is_student_calibrated'),
            params={'student_id': 'another', 'problem_id': '5678'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'total_calibrated_on_so_far': 0,
            'calibrated': False
        })

    def test_grade_peers(self):

        # Ensure a consistent student ID
        student_id = '1234'

        # Check initial number of submissions
        # Should be none graded and 1 required
        self._assert_num_graded(student_id, None, 0, 1)

        # Register a problem that DOES have "peer" in the name
        self._register_problem('test_location', 'Peer Assessed Problem')

        # Retrieve the next submission
        response = requests.get(
            self._peer_url('get_next_submission'),
            params={'grader_id': student_id, 'location': 'test_location'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'submission_id': self.server.DUMMY_DATA['submission_id'],
            'submission_key': self.server.DUMMY_DATA['submission_key'],
            'student_response': self.server.DUMMY_DATA['student_response'],
            'prompt': self.server.DUMMY_DATA['prompt'],
            'rubric': self.server.DUMMY_DATA['rubric'],
            'max_score': self.server.DUMMY_DATA['max_score']
        })

        # Grade the submission
        response = requests.post(
            self._peer_url('save_grade'),
            data={
                'location': 'test_location',
                'grader_id': student_id,
                'submission_id': 1,
                'score': 2,
                'feedback': 'Good job!',
                'submission_key': 'key'
            }
        )
        self._assert_response(response, {'version': 1, 'success': True})

        # Check final number of submissions
        # Shoud be one graded  and none required
        self._assert_num_graded(student_id, 'test_location', 1, 0)

        # Grade the next submission the submission
        response = requests.post(
            self._peer_url('save_grade'),
            data={
                'location': 'test_location',
                'grader_id': student_id,
                'submission_id': 1,
                'score': 2,
                'feedback': 'Good job!',
                'submission_key': 'key'
            }
        )
        self._assert_response(response, {'version': 1, 'success': True})

        # Check final number of submissions
        # Shoud be two graded  and none required
        self._assert_num_graded(student_id, 'test_location', 2, 0)

    def test_problem_list(self):

        self._register_problem('test_location', 'Peer Grading Problem')

        # The problem list returns dummy counts which are not updated
        # The location we use is ignored by the LMS, and we ignore it in the stub,
        # so we use a dummy value there too.
        response = requests.get(
            self._peer_url('get_problem_list'),
            params={'course_id': 'test course'}
        )

        self._assert_response(response, {
            'version': 1, 'success': True,
            'problem_list': [{
                'location': 'test_location',
                'problem_name': 'Peer Grading Problem',
                'num_graded': self.server.DUMMY_DATA['problem_list_num_graded'],
                'num_pending': self.server.DUMMY_DATA['problem_list_num_pending'],
                'num_required': self.server.DUMMY_DATA['problem_list_num_required']
            }]
        })

    def test_ignore_non_peer_problem(self):

        # Register a problem that does NOT have "peer" in the name
        self._register_problem('test_location', 'Self Assessed Problem')

        # Expect that the problem list is empty
        response = requests.get(
            self._peer_url('get_problem_list'),
            params={'course_id': 'test course'}
        )

        self._assert_response(
            response,
            {'version': 1, 'success': True, 'problem_list': []}
        )

        # Expect that no data is available for the problem location
        response = requests.get(
            self._peer_url('get_data_for_location'),
            params={'location': 'test_location', 'student_id': 'test'}
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {'version': 1, 'success': False})

    def test_empty_problem_list(self):

        # Without configuring any problem location, should return an empty list
        response = requests.get(
            self._peer_url('get_problem_list'),
            params={'course_id': 'test course'}
        )
        self._assert_response(response, {'version': 1, 'success': True, 'problem_list': []})

    def _peer_url(self, path):
        """
        Construt a URL to the stub ORA peer-grading service.
        """
        return "http://127.0.0.1:{port}/peer_grading/{path}/".format(
            port=self.server.port, path=path
        )

    def _register_problem(self, location, name):
        """
        Configure the stub to use a particular problem location
        The actual implementation discovers problem locations by submission
        to the XQueue; we do something similar by having the XQueue stub
        register submitted locations with the ORA stub.
        """
        grader_payload = json.dumps({'location': location, 'problem_id': name})
        url = "http://127.0.0.1:{port}/test/register_submission".format(port=self.server.port)
        response = requests.post(url, data={'grader_payload': grader_payload})
        self.assertTrue(response.ok)

    def _assert_response(self, response, expected_json):
        """
        Assert that the `response` was successful and contained
        `expected_json` (dict) as its content.
        """
        self.assertTrue(response.ok)
        self.assertEqual(response.json(), expected_json)

    def _assert_num_graded(self, student_id, location, num_graded, num_required):
        """
        ORA provides two distinct ways to get the submitted/graded counts.
        Here we check both of them to ensure that the number that we've graded
        is consistently `num_graded`.
        """

        # Unlike the actual ORA service,
        # we keep track of counts on a per-student basis.
        # This means that every user starts with N essays to grade,
        # and as they grade essays, that number decreases.
        # We do NOT simulate students adding more essays to the queue,
        # and essays that the current student submits are NOT graded
        # by other students.
        num_pending = StudentState.INITIAL_ESSAYS_AVAILABLE - num_graded

        # Notifications
        response = requests.get(
            self._peer_url('get_notifications'),
            params={'student_id': student_id, 'course_id': 'test course'}
        )
        self._assert_response(response, {
            'version': 1, 'success': True,
            'count_required': num_required,
            'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
            'count_graded': num_graded,
            'count_available': num_pending
        })

        # Location data
        if location is not None:
            response = requests.get(
                self._peer_url('get_data_for_location'),
                params={'location': location, 'student_id': student_id}
            )
            self._assert_response(response, {
                'version': 1, 'success': True,
                'count_required': num_required,
                'student_sub_count': self.server.DUMMY_DATA['student_sub_count'],
                'count_graded': num_graded,
                'count_available': num_pending
            })
