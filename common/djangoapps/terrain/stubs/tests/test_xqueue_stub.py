"""
Unit tests for stub XQueue implementation.
"""

import mock
import unittest
import json
import requests
import time
import copy
from ..xqueue import StubXQueueService, StubXQueueHandler


class StubXQueueServiceTest(unittest.TestCase):

    def setUp(self):
        self.server = StubXQueueService()
        self.url = "http://127.0.0.1:{0}/xqueue/submit".format(self.server.port)
        self.addCleanup(self.server.shutdown)

        # For testing purposes, do not delay the grading response
        self.server.config['response_delay'] = 0

    @mock.patch('terrain.stubs.xqueue.post')
    def test_grade_request(self, post):

        # Post a submission to the stub XQueue
        callback_url = 'http://127.0.0.1:8000/test_callback'
        expected_header = self._post_submission(
            callback_url, 'test_queuekey', 'test_queue',
            json.dumps({
                'student_info': 'test',
                'grader_payload': 'test',
                'student_response': 'test'
            })
        )

        # Check the response we receive
        # (Should be the default grading response)
        expected_body = json.dumps({'correct': True, 'score': 1, 'msg': '<div></div>'})
        self._check_grade_response(post, callback_url, expected_header, expected_body)

    @mock.patch('terrain.stubs.xqueue.post')
    def test_configure_default_response(self, post):

        # Configure the default response for submissions to any queue
        response_content = {'test_response': 'test_content'}
        self.server.config['default'] = response_content

        # Post a submission to the stub XQueue
        callback_url = 'http://127.0.0.1:8000/test_callback'
        expected_header = self._post_submission(
            callback_url, 'test_queuekey', 'test_queue',
            json.dumps({
                'student_info': 'test',
                'grader_payload': 'test',
                'student_response': 'test'
            })
        )

        # Check the response we receive
        # (Should be the default grading response)
        self._check_grade_response(
            post, callback_url, expected_header, json.dumps(response_content)
        )

    @mock.patch('terrain.stubs.xqueue.post')
    def test_configure_specific_response(self, post):

        # Configure the XQueue stub response to any submission to the test queue
        response_content = {'test_response': 'test_content'}
        self.server.config['This is only a test.'] = response_content

        # Post a submission to the XQueue stub
        callback_url = 'http://127.0.0.1:8000/test_callback'
        expected_header = self._post_submission(
            callback_url, 'test_queuekey', 'test_queue',
            json.dumps({'submission': 'This is only a test.'})
        )

        # Check that we receive the response we configured
        self._check_grade_response(
            post, callback_url, expected_header, json.dumps(response_content)
        )

    @mock.patch('terrain.stubs.xqueue.post')
    def test_multiple_response_matches(self, post):

        # Configure the XQueue stub with two responses that
        # match the same submission
        self.server.config['test_1'] = {'response': True}
        self.server.config['test_2'] = {'response': False}

        with mock.patch('terrain.stubs.http.LOGGER') as logger:

            # Post a submission to the XQueue stub
            callback_url = 'http://127.0.0.1:8000/test_callback'
            self._post_submission(
                callback_url, 'test_queuekey', 'test_queue',
                json.dumps({'submission': 'test_1 and test_2'})
            )

            # Wait for the delayed grade response
            self._wait_for_mock_called(logger.error)

            # Expect that we do NOT receive a response
            # and that an error message is logged
            self.assertFalse(post.called)
            self.assertTrue(logger.error.called)

    @mock.patch('terrain.stubs.xqueue.post')
    def test_register_submission_url(self, post):

        # Configure the XQueue stub to notify another service
        # when it receives a submission.
        register_url = 'http://127.0.0.1:8000/register_submission'
        self.server.config['register_submission_url'] = register_url

        callback_url = 'http://127.0.0.1:8000/test_callback'
        submission = json.dumps({'grader_payload': 'test payload'})
        self._post_submission(
            callback_url, 'test_queuekey', 'test_queue', submission
        )

        # Check that a notification was sent
        post.assert_any_call(register_url, data={'grader_payload': u'test payload'})

    def _post_submission(self, callback_url, lms_key, queue_name, xqueue_body):
        """
        Post a submission to the stub XQueue implementation.
        `callback_url` is the URL at which we expect to receive a grade response
        `lms_key` is the authentication key sent in the header
        `queue_name` is the name of the queue in which to send put the submission
        `xqueue_body` is the content of the submission

        Returns the header (a string) we send with the submission, which can
        be used to validate the response we receive from the stub.
        """

        # Post a submission to the XQueue stub
        grade_request = {
            'xqueue_header': json.dumps({
                'lms_callback_url': callback_url,
                'lms_key': 'test_queuekey',
                'queue_name': 'test_queue'
            }),
            'xqueue_body': xqueue_body
        }

        resp = requests.post(self.url, data=grade_request)

        # Expect that the response is success
        self.assertEqual(resp.status_code, 200)

        # Return back the header, so we can authenticate the response we receive
        return grade_request['xqueue_header']

    def _check_grade_response(self, post_mock, callback_url, expected_header, expected_body):
        """
        Verify that the stub sent a POST request back to us
        with the expected data.

        `post_mock` is our mock for `requests.post`
        `callback_url` is the URL we expect the stub to POST to
        `expected_header` is the header (a string) we expect to receive with the grade.
        `expected_body` is the content (a string) we expect to receive with the grade.

        Raises an `AssertionError` if the check fails.
        """
        # Wait for the server to POST back to the callback URL
        # If it takes too long, continue anyway
        self._wait_for_mock_called(post_mock)

        # Check the response posted back to us
        # This is the default response
        expected_callback_dict = {
            'xqueue_header': expected_header,
            'xqueue_body': expected_body,
        }

        # Check that the POST request was made with the correct params
        post_mock.assert_called_with(callback_url, data=expected_callback_dict)

    def _wait_for_mock_called(self, mock_obj, max_time=120):
        """
        Wait for `mock` (a `Mock` object) to be called.
        If seconds elapsed exceeds `max_time`, continue without error.
        """
        start_time = time.time()
        while time.time() - start_time < max_time:
            if mock_obj.called:
                break
            time.sleep(1)
