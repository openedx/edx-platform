# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/projects/tests/test_submissions.py]
"""
import json
import uuid

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from projects.models import Project, Workgroup

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
class SubmissionsApiTests(TestCase):

    """ Test suite for Users API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_users_uri = '/api/users/'
        self.test_workgroups_uri = '/api/workgroups/'
        self.test_projects_uri = '/api/projects/'
        self.test_submissions_uri = '/api/submissions/'

        self.test_course_id = 'edx/demo/course'
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_course_content_id = "i4x://blah"
        self.test_bogus_course_content_id = "14x://foo/bar/baz"

        self.test_document_id = "Document12345.pdf"
        self.test_document_url = "http://test-s3.amazonaws.com/bucketname"
        self.test_document_mime_type = "application/pdf"

        self.test_user = User.objects.create(
            email="test@edx.org",
            username="testing",
            is_active=True
        )

        self.test_workgroup = Workgroup.objects.create(
            name="Test Workgroup",
        )
        self.test_workgroup.users.add(self.test_user)
        self.test_workgroup.save()

        self.test_project = Project.objects.create(
            course_id=self.test_course_id,
            content_id=self.test_course_content_id,
        )
        self.test_project.workgroups.add(self.test_workgroup)
        self.test_project.save()

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

    def test_submissions_list_post(self):
        submission_data = {
            'user': self.test_user.id,
            'project': self.test_project.id,
            'workgroup': self.test_workgroup.id,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_submissions_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['user'], self.test_user.id)
        self.assertEqual(response.data['workgroup'], self.test_workgroup.id)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertEqual(response.data['document_id'], self.test_document_id)
        self.assertEqual(response.data['document_url'], self.test_document_url)
        self.assertEqual(response.data['document_mime_type'], self.test_document_mime_type)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_submissions_list_post_invalid_relationships(self):
        submission_data = {
            'user': 123456,
            'project': self.test_project.id,
            'workgroup': self.test_workgroup.id,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 400)

        submission_data = {
            'user': self.test_user.id,
            'project': 123456,
            'workgroup': self.test_workgroup.id,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 400)

        submission_data = {
            'user': self.test_user.id,
            'project': self.test_project.id,
            'workgroup': 123456,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 400)

    def test_submissions_detail_get(self):
        submission_data = {
            'user': self.test_user.id,
            'project': self.test_project.id,
            'workgroup': self.test_workgroup.id,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_submissions_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.test_submissions_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['user'], self.test_user.id)
        self.assertEqual(response.data['workgroup'], self.test_workgroup.id)
        self.assertEqual(response.data['project'], self.test_project.id)
        self.assertEqual(response.data['document_id'], self.test_document_id)
        self.assertEqual(response.data['document_url'], self.test_document_url)
        self.assertEqual(response.data['document_mime_type'], self.test_document_mime_type)
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_submissions_detail_get_undefined(self):
        test_uri = '/api/submissions/123456789/'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_submnissions_detail_delete(self):
        submission_data = {
            'user': self.test_user.id,
            'project': self.test_project.id,
            'workgroup': self.test_workgroup.id,
            'document_id': self.test_document_id,
            'document_url': self.test_document_url,
            'document_mime_type': self.test_document_mime_type,
        }
        response = self.do_post(self.test_submissions_uri, submission_data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.test_submissions_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
