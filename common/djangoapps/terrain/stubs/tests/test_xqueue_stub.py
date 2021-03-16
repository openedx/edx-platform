"""
Unit tests for stub XQueue implementation.
"""


import ast
import json
import unittest
from unittest import mock

import requests

from ..xqueue import StubXQueueService


class FakeTimer:
    """
    Fake timer implementation that executes immediately.
    """
    def __init__(self, delay, func):  # lint-amnesty, pylint: disable=unused-argument
        self.func = func

    def start(self):
        self.func()


class StubXQueueServiceTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        self.server = StubXQueueService()
        self.url = f"http://127.0.0.1:{self.server.port}/xqueue/submit"
        self.addCleanup(self.server.shutdown)

        # Patch the timer async calls
        patcher = mock.patch('common.djangoapps.terrain.stubs.xqueue.post')
        self.post = patcher.start()
        self.addCleanup(patcher.stop)

        # Patch POST requests
        patcher = mock.patch('common.djangoapps.terrain.stubs.xqueue.Timer')
        timer = patcher.start()
        timer.side_effect = FakeTimer
        self.addCleanup(patcher.stop)

    def test_grade_request(self):

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
        self._check_grade_response(callback_url, expected_header, expected_body)

    def test_configure_default_response(self):

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
        self._check_grade_response(callback_url, expected_header, json.dumps(response_content))

    def test_configure_specific_response(self):

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
        self._check_grade_response(callback_url, expected_header, json.dumps(response_content))

    def test_multiple_response_matches(self):

        # Configure the XQueue stub with two responses that
        # match the same submission
        self.server.config['test_1'] = {'response': True}
        self.server.config['test_2'] = {'response': False}

        with mock.patch('common.djangoapps.terrain.stubs.http.LOGGER') as logger:

            # Post a submission to the XQueue stub
            callback_url = 'http://127.0.0.1:8000/test_callback'
            self._post_submission(
                callback_url, 'test_queuekey', 'test_queue',
                json.dumps({'submission': 'test_1 and test_2'})
            )

            # Expect that we do NOT receive a response
            # and that an error message is logged
            assert not self.post.called
            assert logger.error.called

    def _post_submission(self, callback_url, lms_key, queue_name, xqueue_body):  # lint-amnesty, pylint: disable=unused-argument
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
        assert resp.status_code == 200

        # Return back the header, so we can authenticate the response we receive
        return grade_request['xqueue_header']

    def _check_grade_response(self, callback_url, expected_header, expected_body):
        """
        Verify that the stub sent a POST request back to us
        with the expected data.

        `callback_url` is the URL we expect the stub to POST to
        `expected_header` is the header (a string) we expect to receive with the grade.
        `expected_body` is the content (a string) we expect to receive with the grade.

        Raises an `AssertionError` if the check fails.
        """
        # Check the response posted back to us
        # This is the default response
        expected_callback_dict = {
            'xqueue_header': expected_header,
            'xqueue_body': expected_body,
        }
        # Check that the POST request was made with the correct params
        assert self.post.call_args[1]['data']['xqueue_body'] == expected_callback_dict['xqueue_body']
        assert ast.literal_eval(self.post.call_args[1]['data']['xqueue_header']) ==\
               ast.literal_eval(expected_callback_dict['xqueue_header'])
        assert self.post.call_args[0][0] == callback_url
