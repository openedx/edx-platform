# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_user_views.py]
"""
from random import randint
import simplejson as json
import unittest
import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

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
class UsersApiTests(TestCase):
    """ Test suite for Users API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_first_name = str(uuid.uuid4())
        self.test_last_name = str(uuid.uuid4())

        self.client = SecureClient()
        cache.clear()

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)

        response = self.client.post(uri, headers=headers, content_type='application/json', data=json_data)
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

    def test_user_list_post(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = self.test_server_prefix + test_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['email'], self.test_email)
        self.assertEqual(response.data['username'], local_username)
        self.assertEqual(response.data['first_name'], self.test_first_name)
        self.assertEqual(response.data['last_name'], self.test_last_name)

    def test_user_list_post_duplicate(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)
        self.assertGreater(response.data['message'], 0)
        self.assertEqual(response.data['field_conflict'], 'username')

    def test_user_detail_get(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
        self.assertEqual(len(response.data['resources']), 2)

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

    def test_user_detail_get_undefined(self):
        test_uri = '/api/users/123456789'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_post(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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

    def test_user_groups_list_post_invalid_user(self):
        test_uri = '/api/groups'
        data = {'name': 'Alpha Group'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users/897698769/groups'
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_get(self):
        test_uri = '/api/groups'
        group_name = 'Alpha Group'
        data = {'name': group_name}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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

    def test_user_groups_list_get_invalid_user(self):
        test_uri = '/api/users/123124/groups'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

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
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertEqual(response.data['user_id'], user_id)

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

    def test_user_groups_detail_get_invalid_user(self):
        test_uri = '/api/users/123124/groups/12321'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

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

    def test_user_courses_list_post(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'position': {
                'parent_module_id': str(course.id),
                'child_module_id': str(chapter3.location)

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
        course_id = 'asdfa9sd8fasdf'
        test_uri = '/api/users/{}/courses/{}'.format(str(user_id), course_id)
        position_data = {
            'position': {
                'parent_module_id': course_id,
                'child_module_id': str(chapter1.location)

            }
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_post_position_course_as_module(self):
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
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': course.id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'position': {
                'parent_module_id': str(course.location),
                'child_module_id': str(chapter1.location)

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
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
                'parent_module_id': str(course.location),
                'child_module_id': str(chapter1.location)

            }
        }
        response = self.do_post(confirm_uri, data=position_data)
        self.assertEqual(response.data['position'], chapter1.id)

    def test_user_courses_detail_get_undefined_user(self):
        test_uri = '/api/users/2134234/courses/a8df7asvd98'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_get_undefined_enrollment(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '/api/users/' + str(user_id) + '/courses/' + str(course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_delete(self):
        course = CourseFactory.create()
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
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
        response = self.do_post(post_uri, data)  # Re-enroll the student in the course
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
        test_uri = '/api/users/{}/courses/{}'.format(str(user_id), str(course.id))
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_user_courses_detail_delete_undefined_course(self):
        test_uri = '/api/users'
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/oasdf987sdf'.format(test_uri, str(user_id))
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)
