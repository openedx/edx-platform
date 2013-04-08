import mock
import unittest
import threading
import json
import urllib
import time
from mock_xqueue_server import MockXQueueServer, MockXQueueRequestHandler

from nose.plugins.skip import SkipTest


class MockXQueueServerTest(unittest.TestCase):
    '''
    A mock version of the XQueue server that listens on a local
    port and responds with pre-defined grade messages.

    Used for lettuce BDD tests in lms/courseware/features/problems.feature
    and lms/courseware/features/problems.py

    This is temporary and will be removed when XQueue is
    rewritten using celery.
    '''

    def setUp(self):

        # This is a test of the test setup,
        # so it does not need to run as part of the unit test suite
        # You can re-enable it by commenting out the line below
        raise SkipTest

        # Create the server
        server_port = 8034
        self.server_url = 'http://127.0.0.1:%d' % server_port
        self.server = MockXQueueServer(server_port,
                                       {'correct': True, 'score': 1, 'msg': ''})

        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()

    def test_grade_request(self):

        # Patch post_to_url() so we can intercept
        # outgoing POST requests from the server
        MockXQueueRequestHandler.post_to_url = mock.Mock()

        # Send a grade request
        callback_url = 'http://127.0.0.1:8000/test_callback'

        grade_header = json.dumps({'lms_callback_url': callback_url,
                                   'lms_key': 'test_queuekey',
                                   'queue_name': 'test_queue'})

        grade_body = json.dumps({'student_info': 'test',
                                'grader_payload': 'test',
                                'student_response': 'test'})

        grade_request = {'xqueue_header': grade_header,
                         'xqueue_body': grade_body}

        response_handle = urllib.urlopen(self.server_url + '/xqueue/submit',
                                         urllib.urlencode(grade_request))

        response_dict = json.loads(response_handle.read())

        # Expect that the response is success
        self.assertEqual(response_dict['return_code'], 0)

        # Wait a bit before checking that the server posted back
        time.sleep(3)

        # Expect that the server tries to post back the grading info
        xqueue_body = json.dumps({'correct': True, 'score': 1,
                                  'msg': '<div></div>'})
        expected_callback_dict = {'xqueue_header': grade_header,
                                  'xqueue_body': xqueue_body}
        MockXQueueRequestHandler.post_to_url.assert_called_with(callback_url,
                                                                expected_callback_dict)
