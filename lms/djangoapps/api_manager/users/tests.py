# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_user_views.py]
"""
from random import randint
import json
import unittest
import uuid
from mock import patch
from django.utils.translation import ugettext as _
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings
from student.tests.factories import UserFactory
from student.models import anonymous_id_for_user
from projects.models import Project

from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
@override_settings(EDX_API_KEY=TEST_API_KEY)
@override_settings(PASSWORD_MIN_LENGTH=4)
@override_settings(API_PAGE_SIZE=10)
@patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': True})
class UsersApiTests(TestCase):

    """ Test suite for Users API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_first_name = str(uuid.uuid4())
        self.test_last_name = str(uuid.uuid4())
        self.test_city = str(uuid.uuid4())
        self.org_base_uri = '/api/organizations/'

        self.test_course_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        self.course = CourseFactory.create()
        self.course_content = ItemFactory.create(
            category="videosequence",
            parent_location=self.course.location,
            data=self.test_course_data,
            due="2016-05-16T14:30:00Z",
            display_name="View_Sequence"
        )
        self.test_project = Project.objects.create(
            course_id=self.course.id,
            content_id=self.course_content.id
        )

        self.second_test_project = Project.objects.create(
            course_id=self.course.id + 'b2',
            content_id=self.course_content.id + 'b2'
        )

        self.user = UserFactory()
        self.client = SecureClient()
        cache.clear()

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)

        response = self.client.post(
            uri, headers=headers, content_type='application/json', data=json_data)
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

    def _create_test_user(self):
        """Helper method to create a new test user"""
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        return user_id

    def test_user_list_get(self):
        test_uri = '/api/users'
        users = []
        # create a 25 new users
        for i in xrange(1, 26):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }

            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)
            users.append(response.data['id'])

        # create organizations and add users to them
        total_orgs = 30
        for i in xrange(0, total_orgs):
            data = {
                'name': '{} {}'.format('Org', i),
                'display_name': '{} {}'.format('Org display name', i),
                'users': users
            }
            response = self.do_post(self.org_base_uri, data)
            self.assertEqual(response.status_code, 201)

        # fetch data without any filters applied
        response = self.do_get('{}?page=1'.format(test_uri))
        self.assertEqual(response.status_code, 400)
        # fetch users data with page outside range
        response = self.do_get('{}?ids={}&page=5'.format(test_uri, '2,3,7,11,6,21,34'))
        self.assertEqual(response.status_code, 404)
        # fetch user data by single id
        response = self.do_get('{}?ids={}'.format(test_uri, '3'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(len(response.data['results'][0]['organizations']), total_orgs)
        self.assertIsNotNone(response.data['results'][0]['organizations'][0]['name'])
        self.assertIsNotNone(response.data['results'][0]['organizations'][0]['id'])
        self.assertIsNotNone(response.data['results'][0]['organizations'][0]['url'])
        self.assertIsNotNone(response.data['results'][0]['created'])
        # fetch user data by multiple ids
        response = self.do_get('{}?page_size=5&ids={}'.format(test_uri, '2,3,7,11,6,21,34'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['num_pages'], 2)
        self.assertIn('page=2', response.data['next'])
        self.assertEqual(response.data['previous'], None)
        # fetch user data by username
        response = self.do_get('{}?username={}'.format(test_uri, 'test_user1'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        # fetch user data by email
        response = self.do_get('{}?email={}'.format(test_uri, 'test2@example.com'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['results'][0]['id'])
        # fetch by username with a non existing user
        response = self.do_get('{}?email={}'.format(test_uri, 'john@example.com'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 0)

    def test_user_list_post(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = self.test_server_prefix + \
            test_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertEqual(response.data['username'], local_username)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertEqual(response.data['last_name'], self.test_last_name)
        self.assertIsNotNone(response.data['created'])

    def test_user_list_post_inactive(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password,
            'first_name': self.test_first_name, 'last_name': self.test_last_name, 'is_active': False}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['is_active'], False)

    def test_user_list_post_duplicate(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)
        self.assertGreater(response.data['message'], 0)
        self.assertEqual(response.data['field_conflict'], 'username or email')

    def test_user_detail_get(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertEqual(response.data['username'], local_username)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertEqual(response.data['last_name'], self.test_last_name)
        self.assertEqual(response.data['is_active'], True)
        self.assertEqual(len(response.data['resources']), 2)

    def test_user_detail_get_undefined(self):
        test_uri = '/api/users/123456789'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_detail_post(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email,
                'username': local_username, 'password':self.test_password,
                'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = test_uri + '/' + str(response.data['id'])
        auth_data = {'username': local_username, 'password': self.test_password}
        self.do_post('/api/sessions', auth_data)
        self.assertEqual(response.status_code, 201)
        data = {'is_active': False, 'is_staff': True}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_active'], False)
        self.assertEqual(response.data['is_staff'], True)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertEqual(response.data['username'], local_username)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertEqual(response.data['last_name'], self.test_last_name)
        self.assertEqual(response.data['full_name'], '{} {}'.format(self.test_first_name, self.test_last_name))
        self.assertEqual(response.data['is_active'], False)
        self.assertIsNotNone(response.data['created'])

    def test_user_detail_post_duplicate_username(self):
        """
        Create two users, then pass the same first username in request in order to update username of second user.
        Must return bad request against username, Already exist!
        """
        lst_username = []
        test_uri = '/api/users'
        for i in xrange(2):
            local_username = self.test_username + str(i)
            lst_username.append(local_username)
            data = {
                'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name,
                'last_name': self.test_last_name, 'city': self.test_city, 'country': 'PK', 'level_of_education': 'b', 'year_of_birth': '2000', "gender": 'male', "title": 'Software developer'}
            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)

        data["username"] = lst_username[0]

        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

        # Pass an invalid username in order to update username.
        # Must return bad request against. invalid username!

        data["username"] = '@'
        response = self.do_post(test_uri, data)
        message = _(
            'Username should only consist of A-Z and 0-9, with no spaces.')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], message)

    def test_user_detail_post_invalid_password(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email,
                'username': local_username, 'password': self.test_password,
                'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = test_uri + '/' + str(response.data['id'])
        data = {'password': 'x'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_user_detail_post_user_profile_added_updated(self):
        """
        Create a user, then add the user profile
        Must be added
        """
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name,
            'last_name': self.test_last_name, 'city': self.test_city, 'country': 'PK', 'level_of_education': 'b', 'year_of_birth': '2000',
            'gender': 'male', 'title': 'Software Engineer', 'avatar_url': 'http://example.com/avatar.png'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        self.is_user_profile_created_updated(response, data)

        # Testing profile updating scenario.
        # Must be updated

        data["country"] = "US"
        data["year_of_birth"] = "1990"
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.is_user_profile_created_updated(response, data)

    def test_user_detail_post_profile_added_invalid_year(self):
        """
        Create a user, then add the user profile with invalid year of birth
        Profile Must be added with year_of_birth will be none
        and avatar_url None
        """
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name,
            'last_name': self.test_last_name, 'city': self.test_city, 'country': 'PK', 'level_of_education': 'b', 'year_of_birth': 'abcd',
            'gender': 'male', 'title': 'Software Engineer', 'avatar_url': None}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri_1 = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri_1)
        data["year_of_birth"] = 'None'
        self.is_user_profile_created_updated(response, data)

    def test_user_detail_post_invalid_user(self):
        test_uri = '/api/users/123124124'
        data = {'is_active': False}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_post(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.test_server_prefix + test_uri + '/' + str(group_id)
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['user_id'], str(user_id))

    def test_user_groups_list_post_duplicate(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    def test_user_groups_list_post_invalid_user(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users/897698769/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_get(self):
        test_uri = '/api/groups'
        group_name = 'Alpha Group'
        data = {'name': group_name, 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['groups']), 0)
        self.assertEqual(response.data['groups'][0]['id'], group_id)
        self.assertEqual(response.data['groups'][0]['name'], str(group_name))

    def test_user_groups_list_get_with_query_params(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password,
            'first_name': self.test_first_name, 'last_name': self.test_last_name
        }
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}'.format(test_uri, str(user_id))
        fail_user_id_group_uri = '{}/{}/groups'.format(test_uri, '22')

        group_url = '/api/groups'
        group_name = 'Alpha Group'
        data = {'name': group_name, 'type': 'Engineer'}
        response = self.do_post(group_url, data)
        group_id = response.data['id']
        user_groups_uri = '{}/groups'.format(test_uri)
        data = {'group_id': group_id}
        response = self.do_post(user_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        group_name = 'Beta Group'
        data = {'name': group_name, 'type': 'Architect'}
        response = self.do_post(group_url, data)
        group_id = response.data['id']
        data = {'group_id': group_id}
        response = self.do_post(user_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(fail_user_id_group_uri)
        self.assertEqual(response.status_code, 404)

        response = self.do_get(user_groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 2)

        group_type_uri = '{}?type={}'.format(user_groups_uri, 'Engineer')
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 1)

        error_type_uri = '{}?type={}'.format(user_groups_uri, 'error_type')
        response = self.do_get(error_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 0)

    def test_user_groups_list_get_invalid_user(self):
        test_uri = '/api/users/123124/groups'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_detail_get(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(response.data['id']) + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertEqual(response.data['user_id'], user_id)

    def test_user_groups_detail_delete(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(response.data['id']) + '/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(group_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        response = self.do_delete(
            test_uri)  # Relationship no longer exists, should get a 204 all the same
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_detail_get_invalid_user(self):
        test_uri = '/api/users/123124/groups/12321'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_detail_get_undefined(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '/api/users/' + str(user_id) + '/groups/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_post(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = self.test_server_prefix + test_uri + '/' + course.id
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['id'], course.id)
        self.assertTrue(response.data['is_active'])

    def test_user_courses_list_post_undefined_user(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        user_id = '234234'
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_post_undefined_course(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': '234asdfapsdf'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_get(self):
        course = CourseFactory.create(display_name="TEST COURSE")
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri + '/' + course.id
        self.assertEqual(response.data[0]['uri'], confirm_uri)
        self.assertEqual(response.data[0]['id'], course.id)
        self.assertTrue(response.data[0]['is_active'])
        self.assertEqual(response.data[0]['name'], course.display_name)

    def test_user_courses_list_get_undefined_user(self):
        test_uri = '/api/users/2134234/courses'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_post_position_course_as_descriptor(self):
        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 1"
        )
        chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 2"
        )
        chapter3 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 3"
        )
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'position': {
                'parent_content_id': str(course.id),
                'child_content_id': str(chapter3.location)

            }
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.data['position'], chapter3.id)

    def test_user_courses_detail_post_position_invalid_user(self):
        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 1"
        )
        user_id = 2342334
        course_id = 'asd/fa/9sd8fasdf'
        test_uri = '/api/users/{}/courses/{}'.format(str(user_id), course_id)
        position_data = {
            'position': {
                'parent_content_id': course_id,
                'child_content_id': str(chapter1.location)

            }
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_post_position_course_as_content(self):
        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 1"
        )
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'position': {
                'parent_content_id': str(course.location),
                'child_content_id': str(chapter1.location)

            }
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.data['position'], chapter1.id)

    def test_user_courses_detail_get(self):
        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Overview"
        )
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['course_id'], course.id)
        self.assertEqual(response.data['user_id'], user_id)
        position_data = {
            'position': {
                'parent_content_id': str(course.location),
                'child_content_id': str(chapter1.location)

            }
        }
        response = self.do_post(confirm_uri, data=position_data)
        self.assertEqual(response.data['position'], chapter1.id)

    def test_user_courses_detail_get_undefined_user(self):
        test_uri = '/api/users/2134234/courses/a8df7/asv/d98'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_get_undefined_enrollment(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '/api/users/' + str(user_id) + '/courses/' + str(course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_delete(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        post_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(post_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = post_uri + '/' + str(course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
        response = self.do_post(post_uri, data)
                                # Re-enroll the student in the course
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_delete_undefined_user(self):
        course = CourseFactory.create()
        user_id = '2134234'
        test_uri = '/api/users/{}/courses/{}'.format(
            str(user_id), str(course.id))
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_user_courses_detail_delete_undefined_course(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/oasdf987sdf'.format(test_uri, str(user_id))
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_course_grades_course_not_found(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '/api/users/{}/courses/{}/grades'.format(
            user_id, 'some/unknown/course')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_course_grades_user_not_found(self):
        course = CourseFactory.create()
        test_uri = '/api/users/{}/courses/{}/grades'.format(
            '9999999', course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_get_user_preferences_user_not_found(self):
        test_uri = '/api/users/{}/preferences'.format('999999')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_get_user_preferences_default(self):
        # By default newly created users will have one initial preference settings:
        # 'pref-lang' = 'en'
        user_id = self._create_test_user()
        test_uri = '/api/users/{}/preferences'.format(user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data['pref-lang'], 'en')

    def test_post_user_preferences_user_not_found(self):
        test_uri = '/api/users/{}/preferences'.format('999999')
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 404)

    def test_post_user_preferences_bad_request(self):
        user_id = self._create_test_user()
        test_uri = '/api/users/{}/preferences'.format(user_id)
        response = self.do_post(test_uri, {})
        self.assertEqual(response.status_code, 400)
        # also test with a non-simple key/value set of strings
        response = self.do_post(test_uri, {"an_array": ['1', '2']})
        self.assertEqual(response.status_code, 400)
        response = self.do_post(test_uri, {"an_int": 1})
        self.assertEqual(response.status_code, 400)
        response = self.do_post(test_uri, {"a_float": 1.00})
        self.assertEqual(response.status_code, 400)
        response = self.do_post(test_uri, {"a_boolean": False})
        self.assertEqual(response.status_code, 400)

    def test_post_user_preferences(self):
        user_id = self._create_test_user()
        test_uri = '/api/users/{}/preferences'.format(user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data['pref-lang'], 'en')
        self.assertEqual(response.data['foo'], 'bar')

    def test_update_user_preferences(self):
        user_id = self._create_test_user()
        test_uri = '/api/users/{}/preferences'.format(user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, {"foo": "updated"})
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data['pref-lang'], 'en')
        self.assertEqual(response.data['foo'], 'updated')

    def test_course_grades(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']

        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 1"
        )
        chapter2 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Chapter 2"
        )
        ItemFactory.create(
            category="sequential",
            parent_location=chapter1.location,
            data=test_data,
            display_name="Sequence 1",
        )
        ItemFactory.create(
            category="sequential",
            parent_location=chapter2.location,
            data=test_data,
            display_name="Sequence 2",
        )

        test_uri = '/api/users/{}/courses/{}/grades'.format(
            user_id, course.id)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        courseware_summary = response.data['courseware_summary']
        self.assertEqual(len(courseware_summary), 2)
        self.assertEqual(courseware_summary[0]['course'], 'Robot Super Course')
        self.assertEqual(courseware_summary[0]['display_name'], 'Chapter 1')

        sections = courseware_summary[0]['sections']
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['display_name'], 'Sequence 1')
        self.assertEqual(sections[0]['graded'], False)

        sections = courseware_summary[1]['sections']
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0]['display_name'], 'Sequence 2')
        self.assertEqual(sections[0]['graded'], False)

        grade_summary = response.data['grade_summary']
        self.assertGreater(len(grade_summary['section_breakdown']), 0)
        grading_policy = response.data['grading_policy']
        self.assertGreater(len(grading_policy['GRADER']), 0)
        self.assertIsNotNone(grading_policy['GRADE_CUTOFFS'])

    def is_user_profile_created_updated(self, response, data):
        """This function compare response with user profile data """

        fullname = '{} {}'.format(self.test_first_name, self.test_last_name)
        self.assertEqual(response.data['full_name'], fullname)
        self.assertEqual(response.data['city'], data["city"])
        self.assertEqual(response.data['country'], data["country"])
        self.assertEqual(response.data['gender'], data["gender"])
        self.assertEqual(response.data['title'], data["title"])
        self.assertEqual(response.data['avatar_url'], data["avatar_url"])
        self.assertEqual(
            response.data['level_of_education'], data["level_of_education"])
        self.assertEqual(
            str(response.data['year_of_birth']), data["year_of_birth"])

    def test_user_organizations_list(self):
        user_id = self.user.id
        anonymous_id = anonymous_id_for_user(self.user, self.course.id)
        for i in xrange(1, 7):
            data = {
                'name': 'Org ' + str(i),
                'display_name': 'Org display name' + str(i),
                'users': [user_id]
            }
            response = self.do_post(self.org_base_uri, data)
            self.assertEqual(response.status_code, 201)

        test_uri = '/api/users/{}/organizations/'.format(user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 6)
        self.assertEqual(response.data['num_pages'], 1)

        # test with anonymous user id
        test_uri = '/api/users/{}/organizations/'.format(anonymous_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 6)

        # test with invalid user
        response = self.do_get('/api/users/4356340/organizations/')
        self.assertEqual(response.status_code, 404)

    def test_user_workgroups_list(self):
        test_workgroups_uri = '/api/workgroups/'
        user_id = self.user.id
        # create anonymous user
        anonymous_id = anonymous_id_for_user(self.user, self.course.id)
        for i in xrange(1, 12):
            project_id = self.test_project.id
            if i > 7:  # set to other project
                project_id = self.second_test_project.id
            data = {
                'name': 'Workgroup ' + str(i),
                'project': project_id
            }
            response = self.do_post(test_workgroups_uri, data)
            self.assertEqual(response.status_code, 201)
            test_uri = '{}{}/'.format(test_workgroups_uri, str(response.data['id']))
            users_uri = '{}users/'.format(test_uri)
            data = {"id": user_id}
            response = self.do_post(users_uri, data)
            self.assertEqual(response.status_code, 201)

        # test with anonymous user id
        test_uri = '/api/users/{}/workgroups/?page_size=10'.format(anonymous_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 11)
        self.assertEqual(len(response.data['results']), 10)
        self.assertEqual(response.data['num_pages'], 2)

        # test with course_id filter and integer user id
        response = self.do_get('/api/users/{}/workgroups/?course_id={}'.format(user_id, self.course.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 7)
        self.assertEqual(len(response.data['results']), 7)
        self.assertIsNotNone(response.data['results'][0]['name'])
        self.assertIsNotNone(response.data['results'][0]['project'])

        # test with invalid user
        response = self.do_get('/api/users/4356340/workgroups/')
        self.assertEqual(response.status_code, 404)

        # test with valid user but has no workgroup
        another_user_id = self._create_test_user()
        response = self.do_get('/api/users/{}/workgroups/'.format(another_user_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_user_completions_list(self):
        user_id = self.user.id
        another_user_id = UserFactory().id
        completion_uri = '/api/courses/{}/completions/'.format(self.course.id)

        for i in xrange(1, 17):
            if i > 7:
                course_user_id = another_user_id
            else:
                course_user_id = user_id
            completions_data = {'content_id': '{}_{}'.format(self.course_content.id, i), 'user_id': course_user_id}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

        # Get course module completion by user
        completion_list_uri = '/api/users/{}/courses/{}/completions/?page_size=5'.format(user_id, self.course.id)
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 7)
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['results'][0]['user_id'], user_id)
        self.assertEqual(response.data['results'][0]['course_id'], self.course.id)
        self.assertEqual(response.data['num_pages'], 2)

        # Get course module completion by other user
        completion_list_uri = '/api/users/{}/courses/{}/completions/'.format(another_user_id, self.course.id)
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 9)

        # Get course module completion by other user and course module id
        completion_list_uri = '/api/users/{}/courses/{}/completions/?content_id={}'.format(
            another_user_id,
            self.course.id,
            '{}_{}'.format(self.course_content.id, 10))
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        # Get course module completion by bogus user
        completion_list_uri = '/api/users/{}/courses/{}/completions/'.format('34323422', self.course.id)
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_count_by_city(self):
        test_uri = '/api/users'

        # create a 25 new users
        for i in xrange(1, 26):
            if i < 10:
                city = 'San Francisco'
            elif i < 15:
                city = 'Denver'
            elif i < 20:
                city = 'Dallas'
            else:
                city = 'New York City'
            data = {
                'email': 'test{}@example.com'.format(i), 'username': 'test_user{}'.format(i),
                'password': self.test_password,
                'first_name': self.test_first_name, 'last_name': self.test_last_name, 'city': city,
                'country': 'PK', 'level_of_education': 'b', 'year_of_birth': '2000', 'gender': 'male',
                'title': 'Software Engineer', 'avatar_url': 'http://example.com/avatar.png'
            }

            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)
            response = self.do_get(response.data['uri'])
            self.assertEqual(response.status_code, 200)
            self.is_user_profile_created_updated(response, data)

        response = self.do_get('/api/users/metrics/cities/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['results'][0]['city'], 'San Francisco')
        self.assertEqual(response.data['results'][0]['count'], 9)

        # filter counts by city
        response = self.do_get('/api/users/metrics/cities/?city=new york city')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['city'], 'New York City')
        self.assertEqual(response.data['results'][0]['count'], 6)
