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
from projects.models import Project

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

        self.test_project = Project.objects.create(
            course_id=self.test_course_id,
            content_id=self.test_course_content_id
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
            'project': self.test_project.id
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
        self.assertEqual(response.data['name'], self.test_workgroup_name)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['submissions'])
        self.assertIsNotNone(response.data['workgroup_reviews'])
        self.assertIsNotNone(response.data['peer_reviews'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_workgroups_detail_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['name'], self.test_workgroup_name)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['groups'])
        self.assertIsNotNone(response.data['submissions'])
        self.assertIsNotNone(response.data['workgroup_reviews'])
        self.assertIsNotNone(response.data['peer_reviews'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_workgroups_groups_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
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
        self.assertEqual(response.data['groups'][0]['name'], self.test_group.name)

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

    def test_workgroups_groups_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        groups_uri = '{}groups/'.format(test_uri)
        data = {"id": self.test_group.id}
        response = self.do_post(groups_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_group.id)
        self.assertEqual(response.data[0]['name'], self.test_group.name)

    def test_workgroups_users_post(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        print response.data
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0]['id'], self.test_user.id)

    def test_workgroups_users_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_workgroups_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(users_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_user.id)
        self.assertEqual(response.data[0]['username'], self.test_user.username)
        self.assertEqual(response.data[0]['email'], self.test_user.email)

    def test_workgroups_peer_reviews_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        pr_data = {
            'workgroup': workgroup_id,
            'user': self.test_user.id,
            'reviewer': self.test_user.username,
            'question': 'Test question?',
            'answer': 'Test answer!'
        }
        response = self.do_post('/api/peer_reviews/', pr_data)
        self.assertEqual(response.status_code, 201)
        pr_id = response.data['id']
        test_uri = '{}{}/'.format(self.test_workgroups_uri, workgroup_id)
        peer_reviews_uri = '{}peer_reviews/'.format(test_uri)
        response = self.do_get(peer_reviews_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], pr_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)

    def test_workgroups_workgroup_reviews_get(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
        }
        response = self.do_post(self.test_workgroups_uri, data)
        self.assertEqual(response.status_code, 201)
        workgroup_id = response.data['id']
        wr_data = {
            'workgroup': workgroup_id,
            'reviewer': self.test_user.username,
            'question': 'Test question?',
            'answer': 'Test answer!'
        }
        response = self.do_post('/api/workgroup_reviews/', wr_data)
        self.assertEqual(response.status_code, 201)
        wr_id = response.data['id']
        test_uri = '{}{}/'.format(self.test_workgroups_uri, workgroup_id)
        workgroup_reviews_uri = '{}workgroup_reviews/'.format(test_uri)
        response = self.do_get(workgroup_reviews_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], wr_id)
        self.assertEqual(response.data[0]['reviewer'], self.test_user.username)

    def test_submissions_list_post_invalid_relationships(self):
        data = {
            'name': self.test_workgroup_name,
            'project': self.test_project.id
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
            'project': self.test_project.id
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
