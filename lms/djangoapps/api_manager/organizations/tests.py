# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/organizations/tests.py]
"""
import json
import uuid
import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import Client
from django.test.utils import override_settings

from student.models import UserProfile
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
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
class OrganizationsApiTests(ModuleStoreTestCase):
    """ Test suite for Users API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.base_organizations_uri = '/api/server/organizations/'
        self.base_users_uri = '/api/server/users'
        self.base_groups_uri = '/api/server/groups'
        self.test_organization_name = str(uuid.uuid4())
        self.test_organization_display_name = 'Test Org'
        self.test_organization_contact_name = 'John Org'
        self.test_organization_contact_email = 'john@test.org'
        self.test_organization_contact_phone = '+1 332 232 24234'

        self.test_user_email = str(uuid.uuid4())
        self.test_user_username = str(uuid.uuid4())
        self.test_user = User.objects.create(
            email=self.test_user_email,
            username=self.test_user_username
        )
        profile = UserProfile(user=self.test_user)
        profile.city = 'Boston'
        profile.save()

        self.course = CourseFactory.create()
        self.second_course = CourseFactory.create(
            number="899"
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

    def test_organizations_list_post(self):
        users = []
        for i in xrange(1, 6):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': 'test_pass',
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i),
                'city': 'Boston',
            }
            response = self.do_post(self.base_users_uri, data)
            self.assertEqual(response.status_code, 201)
            users.append(response.data['id'])

        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone,
            'users': users
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = '{}{}{}/'.format(
            self.test_server_prefix,
            self.base_organizations_uri,
            str(response.data['id'])
        )
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['name'], self.test_organization_name)
        self.assertEqual(response.data['display_name'], self.test_organization_display_name)
        self.assertEqual(response.data['contact_name'], self.test_organization_contact_name)
        self.assertEqual(response.data['contact_email'], self.test_organization_contact_email)
        self.assertEqual(response.data['contact_phone'], self.test_organization_contact_phone)
        self.assertIsNotNone(response.data['workgroups'])
        self.assertEqual(len(response.data['users']), len(users))
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_organizations_detail_get(self):
        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['url'], confirm_uri)
        self.assertGreater(response.data['id'], 0)
        self.assertEqual(response.data['name'], self.test_organization_name)
        self.assertEqual(response.data['display_name'], self.test_organization_display_name)
        self.assertEqual(response.data['contact_name'], self.test_organization_contact_name)
        self.assertEqual(response.data['contact_email'], self.test_organization_contact_email)
        self.assertEqual(response.data['contact_phone'], self.test_organization_contact_phone)
        self.assertIsNotNone(response.data['workgroups'])
        self.assertIsNotNone(response.data['users'])
        self.assertIsNotNone(response.data['created'])
        self.assertIsNotNone(response.data['modified'])

    def test_organizations_detail_get_undefined(self):
        test_uri = '{}123456789/'.format(self.base_organizations_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_organizations_detail_delete(self):
        data = {'name': self.test_organization_name}
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_organizations_list_post_invalid(self):
        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': 'testatme.com',
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_organizations_list_post_with_groups(self):
        groups = []
        for i in xrange(1, 6):
            data = {
                'name': '{} {}'.format('Test Group', i),
                'type': 'series',
                'data': {'display_name': 'My first series'}
            }
            response = self.do_post(self.base_groups_uri, data)
            self.assertEqual(response.status_code, 201)
            groups.append(response.data['id'])

        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'groups': groups
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data['groups']), len(groups))

    def test_organizations_users_post(self):
        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['users'][0], self.test_user.id)

    def test_organizations_users_post_invalid_user(self):
        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": 123456}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_organizations_users_get(self):
        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(users_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_user.id)
        self.assertEqual(response.data[0]['username'], self.test_user.username)
        self.assertEqual(response.data[0]['email'], self.test_user.email)

    def test_organizations_users_get_with_course_count(self):
        CourseEnrollmentFactory.create(user=self.test_user, course_id=self.course.id)
        CourseEnrollmentFactory.create(user=self.test_user, course_id=self.second_course.id)

        data = {
            'name': self.test_organization_name,
            'display_name': self.test_organization_display_name,
            'contact_name': self.test_organization_contact_name,
            'contact_email': self.test_organization_contact_email,
            'contact_phone': self.test_organization_contact_phone
        }
        response = self.do_post(self.base_organizations_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}{}/'.format(self.base_organizations_uri, str(response.data['id']))
        users_uri = '{}users/'.format(test_uri)
        data = {"id": self.test_user.id}
        response = self.do_post(users_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get('{}{}'.format(users_uri, '?include_course_counts=True'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['id'], self.test_user.id)
        self.assertEqual(response.data[0]['course_count'], 2)
