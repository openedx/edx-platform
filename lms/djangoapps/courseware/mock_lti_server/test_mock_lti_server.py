"""
Test for Mock_LTI_Server
"""
import mock
from mock import Mock
import unittest
import threading
import textwrap
import urllib
import requests
from mock_lti_server import MockLTIServer


class MockLTIServerTest(unittest.TestCase):
    '''
    A mock version of the LTI provider server that listens on a local
    port and responds with pre-defined grade messages.

    Used for lettuce BDD tests in lms/courseware/features/lti.feature
    '''

    def setUp(self):

        # Create the server
        server_port = 8034
        server_host = 'localhost'
        address = (server_host, server_port)
        self.server = MockLTIServer(address)
        self.server.oauth_settings = {
            'client_key': 'test_client_key',
            'client_secret': 'test_client_secret',
            'lti_base':  'http://{}:{}/'.format(server_host, server_port),
            'lti_endpoint': 'correct_lti_endpoint'
        }
        self.server.run_inside_unittest_flag = True
        #flag for creating right callback_url
        self.server.test_mode = True

        # Start the server in a separate daemon thread
        server_thread = threading.Thread(target=self.server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

    def tearDown(self):

        # Stop the server, freeing up the port
        self.server.shutdown()


    def test_wrong_header(self):
        """
        Tests that LTI server processes request with right program
        path and responses with wrong header.
        """
        #wrong number of params
        payload = {
            'user_id': 'default_user_id',
            'role': 'student',
            'oauth_nonce': '',
            'oauth_timestamp': '',
        }
        uri = self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint']
        headers = {'referer': 'http://localhost:8000/'}
        response = requests.post(uri, data=payload, headers=headers)
        self.assertIn('Incorrect LTI header', response.content)

    def test_wrong_signature(self):
        """
        Tests that LTI server processes request with right program
        path and responses with incorrect signature.
        """
        payload = {
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
            'resource_link_id':'',
        }
        uri = self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint']
        headers = {'referer': 'http://localhost:8000/'}
        response = requests.post(uri, data=payload, headers=headers)
        self.assertIn('Wrong LTI signature', response.content)


    def test_success_response_launch_lti(self):
        """
        Success lti launch.
        """
        payload = {
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
            'resource_link_id':'',
            "lis_outcome_service_url": '',
        }
        self.server.check_oauth_signature = Mock(return_value=True)

        uri = self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint']
        headers = {'referer': 'http://localhost:8000/'}
        response = requests.post(uri, data=payload, headers=headers)
        self.assertIn('This is LTI tool. Success.', response.content)

    def test_send_graded_result(self):

        payload = {
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
            'resource_link_id':'',
            "lis_outcome_service_url": '',
        }
        self.server.check_oauth_signature = Mock(return_value=True)

        uri = self.server.oauth_settings['lti_base'] + self.server.oauth_settings['lti_endpoint']
        #this is the uri for sending grade from lti
        headers = {'referer': 'http://localhost:8000/'}
        response = requests.post(uri, data=payload, headers=headers)

        self.assertTrue('This is LTI tool. Success.' in response.content)
        self.server.grade_data['TC answer'] = "Test response"
        graded_response = requests.post('http://127.0.0.1:8034/grade')
        self.assertIn('Test response', graded_response.content)



