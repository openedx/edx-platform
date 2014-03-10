# pylint: disable=E1101
# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_session_views.py]
"""
from random import randint
import unittest
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
class SessionsApiTests(TestCase):
    """ Test suite for Sessions API views """

    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.base_users_uri = '/api/users'
        self.base_sessions_uri = '/api/sessions'

        self.client = Client()
        cache.clear()

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=data)
        return response

    def do_get(self, uri):
        """Submit an HTTP GET request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.get(uri, headers=headers)
        return response

    def do_delete(self, uri):
        """Submit an HTTP DELETE request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.delete(uri, headers=headers)
        return response

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_list_post_valid(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['token'])
        self.assertGreater(len(response.data['token']), 0)
        self.assertIsNotNone(response.data['uri'])
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.base_sessions_uri + '/' + response.data['token']
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['expires'])
        self.assertGreater(response.data['expires'], 0)
        self.assertIsNotNone(response.data['user'])
        self.assertGreater(len(response.data['user']), 0)
        self.assertIsNotNone(response.data['user']['username'])
        self.assertEqual(str(response.data['user']['username']), local_username)
        self.assertIsNotNone(response.data['user']['id'])
        self.assertEqual(response.data['user']['id'], user_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_list_post_invalid(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        bad_password = "12345"
        data = {'email': self.test_email, 'username': local_username, 'password': bad_password}
        response = self.do_post(self.base_users_uri, data)
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 401)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_list_post_valid_inactive(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user = User.objects.get(username=local_username)
        user.is_active = False
        user.save()
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 403)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_list_post_invalid_notfound(self):
        data = {'username': 'user_12321452334', 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_detail_get(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        test_uri = self.base_sessions_uri + '/' + response.data['token']
        post_token = response.data['token']
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['token'])
        self.assertGreater(len(response.data['token']), 0)
        self.assertEqual(response.data['token'], post_token)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_detail_get_undefined(self):
        test_uri = self.base_sessions_uri + "/123456789"
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_session_detail_delete(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data["uri"]
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
