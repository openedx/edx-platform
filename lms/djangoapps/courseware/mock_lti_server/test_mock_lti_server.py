"""
Test for Mock_LTI_Server
"""
import unittest
import threading
import urllib
from mock_lti_server import MockLTIServer
import requests


class MockLTIServerTest(unittest.TestCase):
    '''
    A mock version of the LTI provider server that listens on a local
    port and responds with pre-defined grade messages.

    Used for lettuce BDD tests in lms/courseware/features/lti.feature
    '''

    def setUp(self):

        # Create the server
        server_port = 8034
        server_host = '127.0.0.1'
        address = (server_host, server_port)
        self.server = MockLTIServer(address)
        self.server.oauth_settings = {
            'client_key': 'test_client_key',
            'client_secret': 'test_client_secret',
            'lti_base':  'http://{}:{}/'.format(server_host, server_port),
            'lti_endpoint': 'correct_lti_endpoint'
        }
        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()

    def test_request(self):
        """
        Tests that LTI server processes request with right program
        path,  and responses with incorrect signature.
        """
        request = {
            'user_id': 'default_user_id',
            'role': 'student',
            'oauth_nonce': '',
            'oauth_timestamp': '',
            'oauth_consumer_key': 'client_key',
            'lti_version': 'LTI-1p0',
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_signature': '',
            'lti_message_type': 'basic-lti-launch-request',
            'oauth_callback': 'about:blank',
            'launch_presentation_return_url': '',
            'lis_outcome_service_url': '',
            'lis_result_sourcedid': ''
        }

        response_handle = urllib.urlopen(
            self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint'],
            urllib.urlencode(request)
        )
        response = response_handle.read()
        self.assertTrue('Wrong LTI signature' in response)

    def test_graded_request(self):
        """
        Tests that LTI server processes a graded request. It should trigger
        the callback URL provided.
        """
        server_port = 8000
        server_host = 'localhost'
        callback_url = 'http://{}:{}/grade_lti'.format(server_host, server_port)

        request = {
            'user_id': 'default_user_id',
            'role': 'student',
            'oauth_nonce': '',
            'oauth_timestamp': '',
            'oauth_consumer_key': 'client_key',
            'lti_version': 'LTI-1p0',
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_signature': '',
            'lti_message_type': 'basic-lti-launch-request',
            'oauth_callback': 'about:blank',
            'launch_presentation_return_url': '',
            'lis_outcome_service_url': '',
            'lis_result_sourcedid': '',

            # TODO: Generate properly.
            "lis_person_sourcedid": "857298237538593757",

            # TODO: Get course based callback URL.
            "lis_outcome_service_url": callback_url,
        }

        response_handle = urllib.urlopen(
            self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint'],
            urllib.urlencode(request)
        )
        response = response_handle.read()
        self.assertTrue('Wrong LTI signature' in response)

        # reading grading result back
        response = requests.get(callback_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, "Hello, Valera and Anton!")
