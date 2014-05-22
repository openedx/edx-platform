# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/projects/tests/test_workgroups.py]
"""
import json
import uuid

from django.contrib.auth.models import Group, User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from api_manager.models import GroupProfile

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
class WorkgroupsApiTests(TestCase):

    """ Test suite for Users API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_workgroups_uri = '/api/workgroups/'
        self.test_course_id = 'edx/demo/course'
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_course_content_id = "i4x://blah"
        self.test_bogus_course_content_id = "14x://foo/bar/baz"
        self.test_group_id = '1'
        self.test_bogus_group_id = "2131241123"
        self.test_workgroup_name = str(uuid.uuid4())

        self.test_group_name = str(uuid.uuid4())
        self.test_group = Group.objects.create(
            name=self.test_group_name
        )
        GroupProfile.objects.create(
            name=self.test_group_name,
            group_id=self.test_group.id,
            group_type="series"
        )

        self.test_user_email = str(uuid.uuid4())
        self.test_user_username = str(uuid.uuid4())
        self.test_user = User.objects.create(
            email=self.test_user_email,
            username=self.test_user_username
        )

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

    def test_workgroups_list_post(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_workgroups_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_workgroups_detail_get(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_workgroups_groups_post(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": self.test_group.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['groups'][0]['id'], self.test_group.id)

        test_groupnoprofile_name = str(uuid.uuid4())
        test_groupnoprofile = Group.objects.create(
            name=test_groupnoprofile_name
        )
        data = {"id": test_groupnoprofile.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['groups'][1]['id'], test_groupnoprofile.id)
        self.assertEqual(response.data['groups'][1]['name'], test_groupnoprofile_name)

    def test_workgroups_users_post(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0]['id'], self.test_user.id)

    def test_submissions_list_post_invalid_relationships(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))

        users_uri = '{}users/'.format(test_uri)
        data = {"id": 123456}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 400)

        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": 123456}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_workgroups_detail_get_undefined(self):
        test_uri = '/api/workgroups/123456789/'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_workgroups_detail_delete(self):
        data = {
            'name': self.test_workgroup_name,
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
