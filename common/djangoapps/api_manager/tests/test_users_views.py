# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_user_views.py]
"""
from random import randint
import unittest
import uuid

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
class UsersApiTests(TestCase):
    """ Test suite for Users API views """

    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_first_name = str(uuid.uuid4())
        self.test_last_name = str(uuid.uuid4())

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
    def test_user_list_post(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['id'])
        self.assertGreater(response.data['id'], 0)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['email'])
        self.assertGreater(len(response.data['email']), 0)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertIsNotNone(response.data['username'])
        self.assertGreater(len(response.data['username']), 0)
        self.assertEqual(response.data['username'], local_username)
        self.assertIsNotNone(response.data['first_name'])
        self.assertGreater(len(response.data['first_name']), 0)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertIsNotNone(response.data['last_name'])
        self.assertGreater(len(response.data['last_name']), 0)
        self.assertEqual(response.data['last_name'], self.test_last_name)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_list_post_duplicate(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)
        self.assertIsNotNone(response.data['message'])
        self.assertGreater(response.data['message'], 0)
        self.assertIsNotNone(response.data['field_conflict'])
        self.assertGreater(response.data['field_conflict'], 0)
        self.assertEqual(response.data['field_conflict'], 'username')

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_detail_get(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['id'])
        self.assertGreater(response.data['id'], 0)
        self.assertIsNotNone(response.data['uri'])
        self.assertGreater(len(response.data['uri']), 0)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['email'])
        self.assertGreater(len(response.data['email']), 0)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertIsNotNone(response.data['username'])
        self.assertGreater(len(response.data['username']), 0)
        self.assertEqual(response.data['username'], local_username)
        self.assertIsNotNone(response.data['first_name'])
        self.assertGreater(len(response.data['first_name']), 0)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertIsNotNone(response.data['last_name'])
        self.assertGreater(len(response.data['last_name']), 0)
        self.assertEqual(response.data['last_name'], self.test_last_name)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_detail_delete(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        response = self.do_delete(test_uri)  # User no longer exists, should get a 204 all the same
        self.assertEqual(response.status_code, 204)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_detail_get_undefined(self):
        test_uri = '/api/users/123456789'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_groups_list_post(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri + '/' + str(response.data['group_id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertIsNotNone(response.data['user_id'])
        self.assertGreater(response.data['user_id'], 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_groups_list_post_duplicate(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_groups_detail_get(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(response.data['id']) + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['uri']), 0)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertIsNotNone(response.data['user_id'])
        self.assertGreater(response.data['user_id'], 0)
        self.assertEqual(response.data['user_id'], user_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_groups_detail_delete(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id']) + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(group_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        response = self.do_delete(test_uri)  # Relationship no longer exists, should get a 204 all the same
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_user_groups_detail_get_undefined(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '/api/users/' + str(user_id) + '/groups/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
