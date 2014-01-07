"""
Unit tests for stub XQueue implementation.
"""

import mock
import unittest
import json
import urllib
import time
from terrain.stubs.xqueue import StubXQueueService


class StubXQueueServiceTest(unittest.TestCase):

    def setUp(self):
        self.server = StubXQueueService()
        self.url = "http://127.0.0.1:{0}".format(self.server.port)
        self.addCleanup(self.server.shutdown)

        # For testing purposes, do not delay the grading response
        self.server.set_config('response_delay', 0)

    @mock.patch('requests.post')
    def test_grade_request(self, post):

        # Send a grade request
        callback_url = 'http://127.0.0.1:8000/test_callback'

        grade_header = json.dumps({
            'lms_callback_url': callback_url,
            'lms_key': 'test_queuekey',
            'queue_name': 'test_queue'
        })

        grade_body = json.dumps({
            'student_info': 'test',
            'grader_payload': 'test',
            'student_response': 'test'
        })

        grade_request = {
            'xqueue_header': grade_header,
            'xqueue_body': grade_body
        }

        response_handle = urllib.urlopen(
            self.url + '/xqueue/submit',
            urllib.urlencode(grade_request)
        )

        response_dict = json.loads(response_handle.read())

        # Expect that the response is success
        self.assertEqual(response_dict['return_code'], 0)

        # Expect that the server tries to post back the grading info
        xqueue_body = json.dumps(
            {'correct': True, 'score': 1, 'msg': '<div></div>'}
        )

        expected_callback_dict = {
            'xqueue_header': grade_header,
            'xqueue_body': xqueue_body
        }

        # Wait for the server to POST back to the callback URL
        # Time out if it takes too long
        start_time = time.time()
        while time.time() - start_time < 5:
            if post.called:
                break

        # Check that the POST request was made with the correct params
        post.assert_called_with(callback_url, data=expected_callback_dict)
