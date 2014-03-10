"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_permissions.py]
"""
from random import randint
import unittest
import uuid

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings

TEST_API_KEY = "123456ABCDEF"


@override_settings(DEBUG=True, EDX_API_KEY=None)
class PermissionsTestsDebug(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def test_has_permission_debug_enabled(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)


@override_settings(DEBUG=False, EDX_API_KEY="123456ABCDEF")
class PermissionsTestsApiKey(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def test_has_permission_valid_api_key(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)


@override_settings(DEBUG=False, EDX_API_KEY=None)
class PermissionsTestDeniedMissingServerKey(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def test_has_permission_missing_server_key(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 403)


@override_settings(DEBUG=False, EDX_API_KEY="67890VWXYZ")
class PermissionsTestDeniedMissingClientKey(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def test_has_permission_invalid_client_key(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 403)


@override_settings(DEBUG=False, EDX_API_KEY="67890VWXYZ")
class PermissionsTestDeniedInvalidClientKey(TestCase):
    """ Test suite for Permissions helper classes """
    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def test_has_permission_invalid_client_key(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 403)
