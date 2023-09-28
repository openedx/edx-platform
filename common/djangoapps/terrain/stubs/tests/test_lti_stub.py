"""
Unit tests for stub LTI implementation.
"""


import unittest
from unittest.mock import Mock, patch

import requests
from urllib.request import urlopen  # pylint: disable=wrong-import-order

from common.djangoapps.terrain.stubs.lti import StubLtiService


class StubLtiServiceTest(unittest.TestCase):
    """
    A stub of the LTI provider that listens on a local
    port and responds with pre-defined grade messages.

    Used for lettuce BDD tests in lms/courseware/features/lti.feature
    """
    def setUp(self):
        super().setUp()
        self.server = StubLtiService()
        self.uri = f'http://127.0.0.1:{self.server.port}/'
        self.launch_uri = self.uri + 'correct_lti_endpoint'
        self.addCleanup(self.server.shutdown)
        self.payload = {
            'user_id': 'default_user_id',
            'roles': 'Student',
            'oauth_nonce': '',
            'oauth_timestamp': '',
            'oauth_consumer_key': 'test_client_key',
            'lti_version': 'LTI-1p0',
            'oauth_signature_method': 'HMAC-SHA1',
            'oauth_version': '1.0',
            'oauth_signature': '',
            'lti_message_type': 'basic-lti-launch-request',
            'oauth_callback': 'about:blank',
            'launch_presentation_return_url': '',
            'lis_outcome_service_url': 'http://localhost:8001/test_callback',
            'lis_result_sourcedid': '',
            'resource_link_id': '',
        }

    def test_invalid_request_url(self):
        """
        Tests that LTI server processes request with right program path but with wrong header.
        """
        self.launch_uri = self.uri + 'wrong_lti_endpoint'
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'Invalid request URL' in response.content

    def test_wrong_signature(self):
        """
        Tests that LTI server processes request with right program
        path and responses with incorrect signature.
        """
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'Wrong LTI signature' in response.content

    @patch('common.djangoapps.terrain.stubs.lti.signature.verify_hmac_sha1', return_value=True)
    def test_success_response_launch_lti(self, check_oauth):  # lint-amnesty, pylint: disable=unused-argument
        """
        Success lti launch.
        """
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'This is LTI tool. Success.' in response.content

    @patch('common.djangoapps.terrain.stubs.lti.signature.verify_hmac_sha1', return_value=True)
    def test_send_graded_result(self, verify_hmac):  # pylint: disable=unused-argument
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'This is LTI tool. Success.' in response.content
        grade_uri = self.uri + 'grade'
        with patch('common.djangoapps.terrain.stubs.lti.requests.post') as mocked_post:
            mocked_post.return_value = Mock(content='Test response', status_code=200)
            response = urlopen(grade_uri, data=b'')  # lint-amnesty, pylint: disable=consider-using-with
            assert b'Test response' in response.read()

    @patch('common.djangoapps.terrain.stubs.lti.signature.verify_hmac_sha1', return_value=True)
    def test_lti20_outcomes_put(self, verify_hmac):  # pylint: disable=unused-argument
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'This is LTI tool. Success.' in response.content
        grade_uri = self.uri + 'lti2_outcome'
        with patch('common.djangoapps.terrain.stubs.lti.requests.put') as mocked_put:
            mocked_put.return_value = Mock(status_code=200)
            response = urlopen(grade_uri, data=b'')  # lint-amnesty, pylint: disable=consider-using-with
            assert b'LTI consumer (edX) responded with HTTP 200' in response.read()

    @patch('common.djangoapps.terrain.stubs.lti.signature.verify_hmac_sha1', return_value=True)
    def test_lti20_outcomes_put_like_delete(self, verify_hmac):  # pylint: disable=unused-argument
        response = requests.post(self.launch_uri, data=self.payload)
        assert b'This is LTI tool. Success.' in response.content
        grade_uri = self.uri + 'lti2_delete'
        with patch('common.djangoapps.terrain.stubs.lti.requests.put') as mocked_put:
            mocked_put.return_value = Mock(status_code=200)
            response = urlopen(grade_uri, data=b'')  # lint-amnesty, pylint: disable=consider-using-with
            assert b'LTI consumer (edX) responded with HTTP 200' in response.read()
