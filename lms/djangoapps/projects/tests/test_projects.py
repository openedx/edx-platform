# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/projects/tests/test_projects.py]
"""
import json
import uuid

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from projects.models import Project, Workgroup
from projects.scope_resolver import GroupProjectParticipantsScopeResolver

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
class ProjectsApiTests(TestCase):

    """ Test suite for Users API views """

    def setUp(self):
        super(ProjectsApiTests, self).setUp()
        self.test_server_prefix = 'https://testserver'
        self.test_projects_uri = '/api/server/projects/'
        self.test_organizations_uri = '/api/server/organizations/'
        self.test_project_name = str(uuid.uuid4())

        self.test_course_id = 'edx/demo/course'
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_course_content_id = "i4x://blah"
        self.test_bogus_course_content_id = "14x://foo/bar/baz"

        self.test_user = User.objects.create(
            email="test@edx.org",
            username="testing",
            is_active=True
        )

        self.test_user2 = User.objects.create(
            email="test2@edx.org",
            username="testing2",
            is_active=True
        )

        self.test_project = Project.objects.create(
            course_id=self.test_course_id,
            content_id=self.test_course_content_id,
        )

        self.test_workgroup = Workgroup.objects.create(
            name="Test Workgroup",
            project=self.test_project,
        )
        self.test_workgroup.add_user(self.test_user)
        self.test_workgroup.save()

        self.test_workgroup2 = Workgroup.objects.create(
            name="Test Workgroup2",
            project=self.test_project,
        )
        self.test_workgroup2.add_user(self.test_user2)
        self.test_workgroup2.save()

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

    def test_projects_list_post(self):
        data = {
            'name': 'Test Organization'
        }
        response = self.do_post(self.test_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_org_id = response.data['id']

        test_course_content_id = "i4x://blahblah1234"
        data = {
            'name': self.test_project_name,
            'course_id': self.test_course_id,
            'content_id': test_course_content_id,
            'organization': test_org_id
        }
        response = self.do_post(self.test_projects_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_projects_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertEqual(response.data['organization'], test_org_id)
        self.assertEqual(response.data['course_id'], self.test_course_id)
        self.assertEqual(response.data['content_id'], test_course_content_id)
        self.assertIsNotNone(response.data['workgroups'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_projects_list_post_without_org(self):
        test_course_content_id = "i4x://blahblah1234"
        data = {
            'name': self.test_project_name,
            'course_id': self.test_course_id,
            'content_id': test_course_content_id,
            'organization': None
        }
        response = self.do_post(self.test_projects_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['organization'], None)

    def test_projects_detail_get(self):
        test_uri = '{}{}/'.format(self.test_projects_uri, self.test_project.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['course_id'], self.test_course_id)
        self.assertEqual(response.data['content_id'], self.test_course_content_id)
        self.assertIsNotNone(response.data['workgroups'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_projects_workgroups_post(self):
        test_uri = '{}{}/workgroups/'.format(self.test_projects_uri, self.test_project.id)
        data = {"id": self.test_workgroup.id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_workgroup.id)

    def test_projects_workgroups_post_invalid_workgroup(self):
        test_uri = '{}{}/workgroups/'.format(self.test_projects_uri, self.test_project.id)
        data = {
            'id': 123456,
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_projects_detail_get_undefined(self):
        test_uri = '{}/123456789/'.format(self.test_projects_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_projects_detail_delete(self):
        test_uri = '{}{}/'.format(self.test_projects_uri, self.test_project.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_get_user_ids(self):
        cursor = Project.get_user_ids_in_project_by_content_id(
            self.test_course_id,
            self.test_course_content_id
        )

        user_ids = [user_id for user_id in cursor.all()]

        self.assertEqual(len(user_ids), 2)
        self.assertIn(self.test_user.id, user_ids)
        self.assertIn(self.test_user2.id, user_ids)

    def test_get_workgroup_user_ids(self):
        cursor = Workgroup.get_user_ids_in_workgroup(self.test_workgroup.id)
        user_ids = [user_id for user_id in cursor.all()]
        self.assertEqual(len(user_ids), 1)
        self.assertIn(self.test_user.id, user_ids)

        cursor = Workgroup.get_user_ids_in_workgroup(self.test_workgroup2.id)
        user_ids = [user_id for user_id in cursor.all()]
        self.assertEqual(len(user_ids), 1)
        self.assertIn(self.test_user2.id, user_ids)

    def test_scope_resolver(self):
        cursor = GroupProjectParticipantsScopeResolver().resolve(
            'group_project_participants',
            {
                'course_id': self.test_course_id,
                'content_id': self.test_course_content_id
            },
            None
        )

        user_ids = [user_id for user_id in cursor.all()]

        self.assertEqual(len(user_ids), 2)
        self.assertIn(self.test_user.id, user_ids)
        self.assertIn(self.test_user2.id, user_ids)

    def test_workgroup_scope_resolver(self):
        cursor = GroupProjectParticipantsScopeResolver().resolve(
            'group_project_workgroup',
            {
                'workgroup_id': self.test_workgroup.id,
            },
            None
        )

        user_ids = [user_id for user_id in cursor.all()]

        self.assertEqual(len(user_ids), 1)
        self.assertIn(self.test_user.id, user_ids)

        cursor = GroupProjectParticipantsScopeResolver().resolve(
            'group_project_workgroup',
            {
                'workgroup_id': self.test_workgroup2.id,
            },
            None
        )

        user_ids = [user_id for user_id in cursor.all()]

        self.assertEqual(len(user_ids), 1)
        self.assertIn(self.test_user2.id, user_ids)
