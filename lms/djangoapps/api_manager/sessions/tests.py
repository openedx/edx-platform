# pylint: disable=E1101
# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_session_views.py]
"""
from random import randint
import uuid
import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):
    """ Django test client using a "secure" connection. """
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
@mock.patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': False,
                                                   'ADVANCED_SECURITY': False,
                                                   'PREVENT_CONCURRENT_LOGINS': False
                                                   })
class SessionsApiTests(TestCase):
    """ Test suite for Sessions API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.base_users_uri = '/api/server/users'
        self.base_sessions_uri = '/api/server/sessions'

        self.client = SecureClient()
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

    def test_session_list_post_valid(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['token']), 0)
        confirm_uri = self.test_server_prefix + self.base_sessions_uri + '/' + response.data['token']
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(response.data['expires'], 0)
        self.assertGreater(len(response.data['user']), 0)
        self.assertEqual(str(response.data['user']['username']), local_username)
        self.assertEqual(response.data['user']['id'], user_id)

    def test_session_list_post_invalid(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        bad_password = "12345"
        data = {'email': self.test_email, 'username': local_username, 'password': bad_password}
        response = self.do_post(self.base_users_uri, data)
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 401)

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

    def test_session_list_post_invalid_notfound(self):
        data = {'username': 'user_12321452334', 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 404)

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
        self.assertEqual(response.data['token'], post_token)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_double_sessions_same_user(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)

        # log in once
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        session1 = response.data['token']

        # test that first session is valid
        test_uri = self.base_sessions_uri + '/' + session1
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        # log in again with the same user
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        session2 = response.data['token']

        # assert that the two sessions keys are not the same
        self.assertNotEqual(session1, session2)

        # test that first session is still valid
        test_uri = self.base_sessions_uri + '/' + session1
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        # test that second session is valid
        test_uri = self.base_sessions_uri + '/' + session2
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        # terminate first session
        test_uri = self.base_sessions_uri + '/' + session1
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

        # test that second session is valid
        test_uri = self.base_sessions_uri + '/' + session2
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        # terminate second session
        test_uri = self.base_sessions_uri + '/' + session2
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_session_detail_get_undefined(self):
        test_uri = self.base_sessions_uri + "/123456789"
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_session_detail_delete(self):
        local_username = self.test_username + str(randint(11, 99))
        local_username = local_username[3:-1]  # username is a 32-character field
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        self.assertEqual(response.status_code, 201)
        data = {'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_sessions_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = self.base_sessions_uri + str(response.data['token'])
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_session_detail_delete_invalid_session(self):
        test_uri = self.base_sessions_uri + "214viouadblah124324blahblah"
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
