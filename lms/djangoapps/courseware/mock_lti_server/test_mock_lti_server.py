import mock
import unittest
import threading
import json
import urllib
import time
from mock_lti_server import MockLTIServer, MockLTIRequestHandler

from nose.plugins.skip import SkipTest


class MockLTIServerTest(unittest.TestCase):
    '''
    A mock version of the LTI provider server that listens on a local
    port and responds with pre-defined grade messages.

    Used for lettuce BDD tests in lms/courseware/features/lti.feature
    '''

    def setUp(self):

        # This is a test of the test setup,
        # so it does not need to run as part of the unit test suite
        # You can re-enable it by commenting out the line below
        # raise SkipTest

        # Create the server
        server_port = 8034
        self.server_url = 'http://127.0.0.1:%d' % server_port
        self.server = MockLTIServer(server_port, {'client_key': '', 'client_secret': ''})

        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()

    def test_oauth_request(self):

        # Send a grade request
        header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            u'Authorization': u'OAuth oauth_nonce="151177408427657509491377691584", \
oauth_timestamp="1377691584", oauth_version="1.0", \
oauth_signature_method="HMAC-SHA1", oauth_consumer_key="", \
oauth_signature="wc1unKXxsX5e4HXJu%2FuiQ1KbrVo%3D"',
            'launch_presentation_return_url': '',
            'user_id': 'default_user_id',
            'lis_result_sourcedid': '',
            'lti_version': 'LTI-1p0',
            'lis_outcome_service_url': '',
            'lti_message_type': 'basic-lti-launch-request',
            'oauth_callback': 'about:blank'
        }
        body = {}
        request = {
            'header': json.dumps(header),
            'body': json.dumps(body)}
        response_handle = urllib.urlopen(
            self.server_url + '/correct_lti_endpoint',
            urllib.urlencode(request)
        )

        response_dict = json.loads(response_handle.read())
        # Expect that the response is success
        self.assertEqual(response_dict['return_code'], 0)
        # self.assertEqual(response_dict['return_code'], 0)

