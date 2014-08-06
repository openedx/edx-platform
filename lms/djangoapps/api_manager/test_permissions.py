"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_permissions.py]
"""
from random import randint
import uuid

from django.test import TestCase
from django.test.utils import override_settings

TEST_API_KEY = "123456ABCDEF"


@override_settings(API_ALLOWED_IP_ADDRESSES=['127.0.0.1', '10.0.2.2', '192.168.0.0/24'])
class PermissionsTests(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.username = self.test_username + str(randint(11, 99))
        self.username = self.username[3:-1]  # username is a 32-character field
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_uri = '/api/server/users'
        self.data = {'email': self.test_email, 'username': self.test_username, 'password': self.test_password}
        self.headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }

    @override_settings(DEBUG=True, EDX_API_KEY=None)
    def test_has_permission_debug_enabled(self):
        response = self._do_post(self.test_uri, self.data, self.headers)
        self.assertEqual(response.status_code, 201)

    @override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
    def test_has_permission_valid_api_key(self):
        response = self._do_post(self.test_uri, self.data, self.headers)
        self.assertEqual(response.status_code, 201)

    @override_settings(DEBUG=False, EDX_API_KEY=None)
    def test_has_permission_missing_server_key(self):
        response = self._do_post(self.test_uri, self.data, self.headers)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, EDX_API_KEY="67890VWXYZ")
    def test_has_permission_invalid_client_key(self):
        headers = {
            'Content-Type': 'application/json',
        }
        response = self._do_post(self.test_uri, self.data, headers)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
    def test_has_permission_invalid_ip_address(self):
        response = self._do_post(self.test_uri, self.data, self.headers, ip_address={'REMOTE_ADDR': '192.1.122.22'})
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
    def test_has_permission_valid_ip_address(self):
        response = self._do_post(self.test_uri, self.data, self.headers, ip_address={'REMOTE_ADDR': '127.0.0.1'})
        self.assertEqual(response.status_code, 201)

    @override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
    def test_invalid_request_header_ip_address(self):
        response = self._do_post(self.test_uri, self.data, self.headers, ip_address={'HTTP_X_FORWARDED_FOR': "192.0.0.2,102.0.0.22"})
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
    def test_valid_subnet_ip_address(self):
        response = self._do_post(self.test_uri, self.data, self.headers, ip_address={'REMOTE_ADDR': "192.168.0.1"})
        self.assertEqual(response.status_code, 201)

    def _do_post(self, uri, data, headers, **kwargs):
        """Submit an HTTP POST request"""

        ip_address = kwargs.get('ip_address', {})
        response = self.client.post(uri, headers=headers, data=data, **ip_address)
        return response
