# pylint: disable=E1101
# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_user_views.py]
"""
from datetime import datetime
from random import randint
import json
import uuid
from urllib import urlencode
from edx_notifications.data import NotificationType, NotificationMessage
from edx_notifications.lib.consumer import get_notifications_count_for_user
from edx_notifications.lib.publisher import register_notification_type, publish_notification_to_user
import mock

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client
from django.test.utils import override_settings
from django.utils import timezone
from django.utils.translation import ugettext as _

from capa.tests.response_xml_factory import StringResponseXMLFactory
from courseware import module_render
from courseware.model_data import FieldDataCache
from django_comment_common.models import Role, FORUM_ROLE_MODERATOR
from instructor.access import allow_access
from notification_prefs import NOTIFICATION_PREF_KEY
from projects.models import Project, Workgroup
from student.tests.factories import UserFactory
from student.models import anonymous_id_for_user
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from openedx.core.djangoapps.user_api.models import UserPreference
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from django.contrib.auth.models import User
from openedx.core.djangoapps.user_api.models import UserPreference
from notification_prefs import NOTIFICATION_PREF_KEY

TEST_API_KEY = str(uuid.uuid4())


def _fake_get_user_social_stats(user_id, course_id, end_date=None):
    if not end_date:
        raise Exception('Expected None end_date parameter')

    return {
        '1': {'foo':'bar'}
    }

def _fake_get_user_social_stats_with_end(user_id, course_id, end_date=None):
    if not end_date:
        raise Exception('Expected non-None end_date parameter')

    return {
        '1': {'foo':'bar'}
    }

class SecureClient(Client):

    """ Django test client using a "secure" connection. """

    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(DEBUG=True)
@override_settings(EDX_API_KEY=TEST_API_KEY)
@override_settings(PASSWORD_MIN_LENGTH=4)
@override_settings(API_PAGE_SIZE=10)
@mock.patch.dict("django.conf.settings.FEATURES", {'ENFORCE_PASSWORD_POLICY': True})
class UsersApiTests(ModuleStoreTestCase):
    """ Test suite for Users API views """

    def get_module_for_user(self, user, course, problem):
        """Helper function to get useful module at self.location in self.course_id for user"""
        mock_request = mock.MagicMock()
        mock_request.user = user
        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            course.id, user, course, depth=2)
        module = module_render.get_module(  # pylint: disable=protected-access
            user,
            mock_request,
            problem.location,
            field_data_cache,
            course.id
        )
        return module

    def setUp(self):
        super(UsersApiTests, self).setUp()
        self.test_server_prefix = 'https://testserver'
        self.test_username = str(uuid.uuid4())
        self.test_password = 'Test.Me64!'
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_first_name = str(uuid.uuid4())
        self.test_last_name = str(uuid.uuid4())
        self.test_city = str(uuid.uuid4())
        self.courses_base_uri = '/api/server/courses'
        self.groups_base_uri = '/api/server/groups'
        self.org_base_uri = '/api/server/organizations/'
        self.workgroups_base_uri = '/api/server/workgroups/'
        self.projects_base_uri = '/api/server/projects/'
        self.users_base_uri = '/api/server/users'
        self.sessions_base_uri = '/api/server/sessions'
        self.test_bogus_course_id = 'foo/bar/baz'
        self.test_bogus_content_id = 'i4x://foo/bar/baz/Chapter1'

        self.test_course_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        self.course = CourseFactory.create(
            display_name="TEST COURSE",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        self.course_content = ItemFactory.create(
            category="videosequence",
            parent_location=self.course.location,
            data=self.test_course_data,
            due=datetime(2016, 5, 16, 14, 30),
            display_name="View_Sequence"
        )
        self.course2 = CourseFactory.create(display_name="TEST COURSE2", org='TESTORG2')
        self.course2_content = ItemFactory.create(
            category="videosequence",
            parent_location=self.course2.location,
            data=self.test_course_data,
            due=datetime(2016, 5, 16, 14, 30),
            display_name="View_Sequence2"
        )

        self.user = UserFactory()
        self.client = SecureClient()
        cache.clear()

        Role.objects.get_or_create(
            name=FORUM_ROLE_MODERATOR,
            course_id=self.course.id)

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)

        response = self.client.post(
            uri, headers=headers, content_type='application/json', data=json_data)
        return response

    def do_put(self, uri, data):
        """Submit an HTTP PUT request"""
        headers = {
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        json_data = json.dumps(data)

        response = self.client.put(
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
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        return user_id

    def test_user_is_staff(self):
        """
        Test if a user is a staff member
        """
        test_uri = self.users_base_uri
        for i in xrange(1, 7):
            data = {
                    'email': 'test{}@example.com'.format(i),
                    'username': 'test_user{}'.format(i),
                    'password': 'PassWord1',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'city': 'Boston',
            }
            data['is_staff'] = True if i % 2 == 0 else False

            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)

        # Test for Robot user with ID 1
        response = self.do_get('{}?ids={}'.format(test_uri, '1,2,3,4,5,6,7'))
        self.assertEqual(response.status_code, 200)

        # ID 1 is a Robot Test (results[0]) so the users list starts with ID 2 (results[1])
        self.assertEqual(response.data['results'][1]['is_staff'], False)        
        self.assertEqual(response.data['results'][3]['is_staff'], False)        
        self.assertEqual(response.data['results'][5]['is_staff'], False)        
        self.assertTrue(response.data['results'][2]['is_staff'])
        self.assertTrue(response.data['results'][4]['is_staff'])
        self.assertTrue(response.data['results'][6]['is_staff'])

    def test_user_list_get(self):
        test_uri = self.users_base_uri
        users = []
        # create a 25 new users
        for i in xrange(1, 26):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': self.test_password,
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i),
                'avatar_url': 'http://avatar.com/{}.jpg'.format(i),
                'city': 'Boston',
                'title': "The King",
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
        response = self.do_get('{}?ids={}'.format(test_uri, '23'))
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
        # add some additional fields and filter the response to only these fields
        response = self.do_get('{}?email=test2@example.com&fields=avatar_url,city,title'.format(test_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['avatar_url'], 'http://avatar.com/2.jpg')
        self.assertEqual(response.data['results'][0]['city'], 'Boston')
        self.assertEqual(response.data['results'][0]['title'], 'The King')
        if 'id' in response.data['results'][0]:
            self.fail("Dynamic field filtering error in UserSerializer")

    def test_user_list_get_with_org_filter(self):
        test_uri = self.users_base_uri
        users = []
        # create a 7 new users
        for i in xrange(1, 8):
            data = {
                'email': 'test{}@example.com'.format(i),
                'username': 'test_user{}'.format(i),
                'password': self.test_password,
                'first_name': 'John{}'.format(i),
                'last_name': 'Doe{}'.format(i)
            }

            response = self.do_post(test_uri, data)
            self.assertEqual(response.status_code, 201)
            users.append(response.data['id'])

        # create organizations and add users to them
        total_orgs = 4
        for i in xrange(1, total_orgs):
            data = {
                'name': '{} {}'.format('Org', i),
                'display_name': '{} {}'.format('Org display name', i),
                'users': users[:i]
            }
            response = self.do_post(self.org_base_uri, data)
            self.assertEqual(response.status_code, 201)

        # fetch users without any organization association
        response = self.do_get('{}?has_organizations=true'.format(test_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 3)
        self.assertIsNotNone(response.data['results'][0]['is_active'])

        response = self.do_get('{}?has_organizations=false'.format(test_uri))
        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data['results']), 4)

    def test_user_list_post(self):
        test_uri = self.users_base_uri
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
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password,
            'first_name': self.test_first_name, 'last_name': self.test_last_name, 'is_active': False}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['is_active'], False)

    def test_user_list_post_duplicate(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)
        self.assertGreater(response.data['message'], 0)
        self.assertEqual(response.data['field_conflict'], 'username or email')

    @mock.patch.dict("student.models.settings.FEATURES", {"ENABLE_DISCUSSION_EMAIL_DIGEST": True})
    def test_user_list_post_discussion_digest_email(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = self.test_server_prefix + \
            test_uri + '/' + str(response.data['id'])
        user = User.objects.get(id=response.data['id'])
        self.assertIsNotNone(UserPreference.get_preference(user, NOTIFICATION_PREF_KEY))

    def test_user_detail_get(self):
        test_uri = self.users_base_uri
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
        test_uri = '{}/123456789'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_detail_post(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email,
                'username': local_username, 'password': self.test_password,
                'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = test_uri + '/' + str(response.data['id'])
        auth_data = {'username': local_username, 'password': self.test_password}
        self.do_post(self.sessions_base_uri, auth_data)
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

    def test_user_detail_invalid_email(self):
        test_uri = '{}/{}'.format(self.users_base_uri, self.user.id)
        data = {
            'email': 'fail'
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid email address', response.content)

    def test_user_detail_duplicate_email(self):
        user2 = UserFactory()
        test_uri = '{}/{}'.format(self.users_base_uri, self.user.id)
        test_uri2 = '{}/{}'.format(self.users_base_uri, user2.id)
        data = {
            'email': self.test_email
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_post(test_uri2, data)
        self.assertEqual(response.status_code, 400)
        self.assertIn('A user with that email address already exists.', response.content)

    def test_user_detail_email_updated(self):
        test_uri = '{}/{}'.format(self.users_base_uri, self.user.id)
        new_email = 'test@example.com'
        data = {
            'email': new_email
        }
        self.assertNotEqual(self.user.email, new_email)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        self.user = User.objects.get(id=self.user.id)
        self.assertEqual(self.user.email, new_email)

    def test_user_detail_post_duplicate_username(self):
        """
        Create two users, then pass the same first username in request in order to update username of second user.
        Must return bad request against username, Already exist!
        """
        lst_username = []
        test_uri = self.users_base_uri
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
        test_uri = self.users_base_uri
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
        test_uri = self.users_base_uri
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

        data['first_name'] = "First Name"
        data['last_name'] = "Surname"
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.is_user_profile_created_updated(response, data)

        data["country"] = "US"
        data["year_of_birth"] = "1990"
        data["title"] = ""
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
        test_uri = self.users_base_uri
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
        test_uri = '{}/123124124'.format(self.users_base_uri)
        data = {'is_active': False}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_post(self):
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
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
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
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
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = '{}/897698769/groups'.format(self.users_base_uri)
        data = {'group_id': group_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_list_get(self):
        test_uri = self.groups_base_uri
        group_name = 'Alpha Group'
        data = {'name': group_name, 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name, 'title': 'The King'}
        response = self.do_post(test_uri, data)
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
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email, 'username': local_username, 'password': self.test_password,
            'first_name': self.test_first_name, 'last_name': self.test_last_name
        }
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}'.format(test_uri, str(user_id))
        fail_user_id_group_uri = '{}/{}/groups'.format(self.users_base_uri, '22')

        group_url = self.groups_base_uri
        group_name = 'Alpha Group'
        group_xblock_id = 'location:GroupTester+TG101+1+group-project+079879fdabae47f6848f38a58f41f2c7'
        group_test_value = 'values 2'
        group_data = {
            'xblock_id': group_xblock_id,
            'key2': group_test_value
        }
        data = {'name': group_name, 'type': 'Engineer', 'data': group_data}
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

        course_id = unicode(self.course.id)
        response = self.do_post('{}/{}/courses/'.format(group_url, group_id), {'course_id': course_id})
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

        course = {'course': course_id}
        group_type_uri = '{}?{}'.format(user_groups_uri, urlencode(course))
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 1)
        self.assertEqual(response.data['groups'][0]['id'], group_id)

        group_data_filters = {
            'data__xblock_id': group_xblock_id,
            'data__key2': group_test_value
        }
        group_type_uri = '{}?{}'.format(user_groups_uri, urlencode(group_data_filters))
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 1)

        group_type_uri = '{}?{}'.format(user_groups_uri, urlencode({'data__key2': group_test_value}))
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 1)

        group_type_uri = '{}?{}'.format(user_groups_uri, urlencode({'data__xblock_id': 'invalid_value',
                                                                    'data__key2': group_test_value}))
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 0)

        group_type_uri = '{}?{}'.format(user_groups_uri, urlencode({'data__key2': 'invalid_value'}))
        response = self.do_get(group_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 0)

        error_type_uri = '{}?type={}'.format(user_groups_uri, 'error_type')
        response = self.do_get(error_type_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['groups']), 0)

    def test_user_groups_list_get_invalid_user(self):
        test_uri = '{}/123124/groups'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_detail_get(self):
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
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
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
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
        test_uri = '{}/123124/groups/12321'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_groups_detail_get_undefined(self):
        test_uri = self.groups_base_uri
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(test_uri, data)
        group_id = response.data['id']
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/groups/{}'.format(self.users_base_uri, user_id, group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_post(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': unicode(self.course.id)}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = self.test_server_prefix + test_uri + '/' + unicode(self.course.id)
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['id'], unicode(self.course.id))
        self.assertTrue(response.data['is_active'])

    def test_user_courses_list_post_undefined_user(self):
        course = CourseFactory.create()
        test_uri = self.users_base_uri
        user_id = '234234'
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': unicode(course.id)}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_post_undefined_course(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))
        data = {'course_id': '234asdfapsdf/2sdfs/sdf'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)
        data = {'course_id': 'really-invalid-course-id-oh-boy-watch-out'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_list_get(self):
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses'.format(test_uri, str(user_id))

        data = {'course_id': unicode(self.course.id)}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = self.test_server_prefix + test_uri + '/' + unicode(self.course.id)

        course_with_out_date_values = CourseFactory.create()
        data = {'course_id': unicode(course_with_out_date_values.id)}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri + '/' + unicode(course_with_out_date_values.id)
        self.assertEqual(response.data[0]['uri'], confirm_uri)
        self.assertEqual(response.data[0]['id'], unicode(course_with_out_date_values.id))
        self.assertTrue(response.data[0]['is_active'])
        self.assertEqual(response.data[0]['name'], course_with_out_date_values.display_name)
        self.assertEqual(response.data[0]['start'], course_with_out_date_values.start)
        self.assertEqual(response.data[0]['end'], course_with_out_date_values.end)
        self.assertEqual(datetime.strftime(response.data[1]['start'], '%Y-%m-%d %H:%M:%S'), datetime.strftime(self.course.start, '%Y-%m-%d %H:%M:%S'))
        self.assertEqual(datetime.strftime(response.data[1]['end'], '%Y-%m-%d %H:%M:%S'), datetime.strftime(self.course.end, '%Y-%m-%d %H:%M:%S'))

    def test_user_courses_list_get_undefined_user(self):
        test_uri = '{}/2134234/courses'.format(self.users_base_uri)
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
        sequential1 = ItemFactory.create(
            category="sequential",
            parent_location=chapter3.location,
            data=test_data,
            display_name="Sequential 1"
        )
        sequential2 = ItemFactory.create(
            category="sequential",
            parent_location=chapter3.location,
            data=test_data,
            display_name="Sequential 2"
        )
        vertical1 = ItemFactory.create(
            category="vertical",
            parent_location=sequential2.location,
            data=test_data,
            display_name="Vertical 1"
        )
        vertical2 = ItemFactory.create(
            category="vertical",
            parent_location=sequential2.location,
            data=test_data,
            display_name="Vertical 2"
        )
        vertical3 = ItemFactory.create(
            category="vertical",
            parent_location=sequential2.location,
            data=test_data,
            display_name="Vertical 3"
        )

        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': unicode(course.id)}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + unicode(course.id)
        self.assertEqual(response.status_code, 201)

        position_data = {
            'positions': [
                {
                    'parent_content_id': unicode(course.id),
                    'child_content_id': str(chapter3.location)
                },
                {
                    'parent_content_id': unicode(chapter3.scope_ids.usage_id),
                    'child_content_id': str(sequential2.location)
                },
                {
                    'parent_content_id': unicode(sequential2.scope_ids.usage_id),
                    'child_content_id': str(vertical3.location)
                }
            ]
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.data['positions'][0], unicode(chapter3.scope_ids.usage_id))
        self.assertEqual(response.data['positions'][1], unicode(sequential2.scope_ids.usage_id))
        self.assertEqual(response.data['positions'][2], unicode(vertical3.scope_ids.usage_id))

        response = self.do_get(response.data['uri'])
        self.assertEqual(response.data['position_tree']['chapter']['id'], unicode(chapter3.scope_ids.usage_id))
        self.assertEqual(response.data['position_tree']['sequential']['id'], unicode(sequential2.scope_ids.usage_id))
        self.assertEqual(response.data['position_tree']['vertical']['id'], unicode(vertical3.scope_ids.usage_id))

    def test_user_courses_detail_post_invalid_course(self):
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, self.user.id, self.test_bogus_course_id)
        response = self.do_post(test_uri, data={})
        self.assertEqual(response.status_code, 404)

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
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, user_id, course_id)
        position_data = {
            'positions': [
                {
                    'parent_content_id': course_id,
                    'child_content_id': str(chapter1.location)

                }
            ]
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
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': unicode(course.id)}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'positions': [
                {
                    'parent_content_id': str(course.location),
                    'child_content_id': str(chapter1.location)

                }
            ]
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.data['positions'][0], unicode(chapter1.scope_ids.usage_id))

    def test_user_courses_detail_post_position_invalid_course(self):
        test_uri = '{}/{}/courses'.format(self.users_base_uri, self.user.id)
        data = {'course_id': unicode(self.course.id)}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + unicode(self.course.id)
        self.assertEqual(response.status_code, 201)
        position_data = {
            'positions': [
                {
                    'parent_content_id': self.test_bogus_course_id,
                    'child_content_id': self.test_bogus_content_id
                }
            ]
        }
        response = self.do_post(test_uri, data=position_data)
        self.assertEqual(response.status_code, 400)

    def test_user_courses_detail_get(self):
        course = CourseFactory.create()
        test_data = '<html>{}</html>'.format(str(uuid.uuid4()))
        chapter1 = ItemFactory.create(
            category="chapter",
            parent_location=course.location,
            data=test_data,
            display_name="Overview"
        )
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': unicode(course.id)}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + unicode(course.id)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['course_id'], unicode(course.id))
        self.assertEqual(response.data['user_id'], user_id)
        position_data = {
            'positions': [
                {
                    'parent_content_id': unicode(course.id),
                    'child_content_id': unicode(chapter1.scope_ids.usage_id)

                }
            ]
        }
        response = self.do_post(confirm_uri, data=position_data)
        self.assertEqual(response.data['positions'][0], unicode(chapter1.scope_ids.usage_id))
        response = self.do_get(confirm_uri)
        self.assertGreater(response.data['position'], 0) # Position in the GET response is an integer!
        self.assertEqual(response.data['position_tree']['chapter']['id'], unicode(chapter1.scope_ids.usage_id))

    def test_user_courses_detail_get_invalid_course(self):
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, self.user.id, self.test_bogus_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_get_undefined_user(self):
        test_uri = '{}/2134234/courses/a8df7/asv/d98'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_get_undefined_enrollment(self):
        course = CourseFactory.create()
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, user_id, course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_detail_delete(self):
        course = CourseFactory.create()
        test_uri = self.users_base_uri
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password':
                self.test_password, 'first_name': self.test_first_name, 'last_name': self.test_last_name}
        response = self.do_post(test_uri, data)
        user_id = response.data['id']
        post_uri = test_uri + '/' + str(user_id) + '/courses'
        data = {'course_id': unicode(course.id)}
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
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, user_id, course.id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_user_courses_detail_delete_undefined_course(self):
        test_uri = '{}/{}/courses/{}'.format(self.users_base_uri, self.user.id, self.test_bogus_course_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_user_course_grades_course_not_found(self):
        test_uri = '{}/{}/courses/some/unknown/course/grades'.format(self.users_base_uri, self.user.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_course_grades_user_not_found(self):
        course = CourseFactory.create()
        test_uri = '{}/99999999/courses/{}/grades'.format(self.users_base_uri, course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_preferences_user_list_get_not_found(self):
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, '999999')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_preferences_list_get_default(self):
        # By default newly created users will have one initial preference settings:
        # 'pref-lang' = 'en'
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data['pref-lang'], 'en')

    def test_user_preferences_list_post_user_not_found(self):
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, '999999')
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 404)

    def test_user_preferences_list_post_bad_request(self):
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
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

    def test_user_preferences_list_post(self):
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data['pref-lang'], 'en')
        self.assertEqual(response.data['foo'], 'bar')

    def test_user_preferences_list_update(self):
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, {"foo": "updated"})
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data['pref-lang'], 'en')
        self.assertEqual(response.data['foo'], 'updated')

    def test_user_preferences_detail_get(self):
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        test_uri = '{}/{}'.format(test_uri, 'foo')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['foo'], 'bar')

    def test_user_preferences_detail_get_invalid_user(self):
        test_uri = '{}/12345/preferences/foo'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_preferences_detail_delete(self):
        user_id = self._create_test_user()
        test_uri = '{}/{}/preferences'.format(self.users_base_uri, user_id)
        response = self.do_post(test_uri, {"foo": "bar"})
        self.assertEqual(response.status_code, 201)
        test_uri = '{}/{}'.format(test_uri, 'foo')
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_preferences_detail_delete_invalid_user(self):
        test_uri = '{}/12345/preferences/foo'.format(self.users_base_uri)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_courses_grades_list_get(self):
        user_id = self.user.id

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

        ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='foo'),
            metadata={'rerandomize': 'always'},
            display_name="test problem 1",
            max_grade=45
        )

        problem = ItemFactory.create(
            parent_location=chapter2.location,
            category='problem',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            metadata={'rerandomize': 'always'},
            display_name="test problem 2"
        )

        item = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='foo'),
            display_name=u"test mentoring midterm",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Midterm Exam"}
        )
        points_scored = 1
        points_possible = 1
        user = self.user
        module = self.get_module_for_user(user, course, item)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item2 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring final",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Final Exam"}
        )
        points_scored = 95
        points_possible = 100
        user = self.user
        module = self.get_module_for_user(user, course, item2)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item3 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        points_scored = 7
        points_possible = 10
        user = self.user
        module = self.get_module_for_user(user, course, item3)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item4 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        points_scored = 9
        points_possible = 10
        user = self.user
        module = self.get_module_for_user(user, course, item4)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item5 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework 3",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"},
            due=datetime(2015, 1, 16, 14, 30).replace(tzinfo=timezone.utc)
        )
        points_scored = 1
        points_possible = 1
        user = self.user
        module = self.get_module_for_user(user, course, item)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item2 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring final",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Final Exam"}
        )
        points_scored = 95
        points_possible = 100
        user = self.user
        module = self.get_module_for_user(user, course, item2)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item3 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        points_scored = 7
        points_possible = 10
        user = self.user
        module = self.get_module_for_user(user, course, item3)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item4 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework 2",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"}
        )
        points_scored = 9
        points_possible = 10
        user = self.user
        module = self.get_module_for_user(user, course, item4)
        grade_dict = {'value': points_scored, 'max_value': points_possible, 'user_id': user.id}
        module.system.publish(module, 'grade', grade_dict)

        item5 = ItemFactory.create(
            parent_location=chapter2.location,
            category='mentoring',
            data=StringResponseXMLFactory().build_xml(answer='bar'),
            display_name=u"test mentoring homework 3",
            metadata={'rerandomize': 'always', 'graded': True, 'format': "Homework"},
            due=datetime(2015, 1, 16, 14, 30).replace(tzinfo=timezone.utc)
        )



        test_uri = '{}/{}/courses/{}/grades'.format(self.users_base_uri, user_id, unicode(course.id))

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
        self.assertEqual(len(sections), 8)
        self.assertEqual(sections[0]['display_name'], 'Sequence 2')
        self.assertEqual(sections[0]['graded'], False)

        grade_summary = response.data['grade_summary']
        self.assertGreater(len(grade_summary['section_breakdown']), 0)
        grading_policy = response.data['grading_policy']
        self.assertGreater(len(grading_policy['GRADER']), 0)
        self.assertIsNotNone(grading_policy['GRADE_CUTOFFS'])

        self.assertEqual(response.data['current_grade'], 0.7)
        self.assertEqual(response.data['proforma_grade'], 0.9375)

        test_uri = '{}/{}/courses/grades'.format(self.users_base_uri, user_id)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['course_id'], unicode(course.id))
        self.assertEqual(response.data[0]['current_grade'], 0.73)
        self.assertEqual(response.data[0]['proforma_grade'], 0.9375)
        self.assertEqual(response.data[0]['complete_status'], False)

    def is_user_profile_created_updated(self, response, data):
        """This function compare response with user profile data """

        first_name = data.get('first_name', self.test_first_name)
        last_name = data.get('last_name', self.test_last_name)
        fullname = '{} {}'.format(first_name, last_name)
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
        # This one's technically on the user model itself, but can be updated.
        self.assertEqual(response.data['email'], data['email'])

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

        test_uri = '{}/{}/organizations/'.format(self.users_base_uri, user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 6)
        self.assertEqual(len(response.data['results']), 6)
        self.assertEqual(response.data['num_pages'], 1)

        # test with anonymous user id
        test_uri = '{}/{}/organizations/'.format(self.users_base_uri, anonymous_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 6)

        # test with invalid user
        response = self.do_get('{}/4356340/organizations/'.format(self.users_base_uri))
        self.assertEqual(response.status_code, 404)

    def test_user_workgroups_list(self):
        test_workgroups_uri = self.workgroups_base_uri
        project_1 = Project.objects.create(
            course_id=unicode(self.course.id),
            content_id=unicode(self.course_content.scope_ids.usage_id),
        )
        p1_workgroup_1 = Workgroup.objects.create(
            name = 'Workgroup 1',
            project = project_1
        )

        project_2 = Project.objects.create(
            course_id=unicode(self.course2.id),
            content_id=unicode(self.course2_content.scope_ids.usage_id),
        )
        p2_workgroup_1 = Workgroup.objects.create(
            name = 'Workgroup 2',
            project = project_2
        )
        for i in xrange(1,12):
            test_user = UserFactory()
            users_uri = '{}{}/users/'.format(self.workgroups_base_uri, 1)
            data = {"id": test_user.id}
            response = self.do_post(users_uri, data)
            self.assertEqual(response.status_code, 201)
            if test_user.id > 6:
                users_uri = '{}{}/users/'.format(self.workgroups_base_uri, 2)
                data = {"id": test_user.id}
                response = self.do_post(users_uri, data)
                self.assertEqual(response.status_code, 201)

        # test with anonymous user id
        anonymous_id = anonymous_id_for_user(test_user, self.course.id)
        test_uri = '{}/{}/workgroups/?page_size=1'.format(self.users_base_uri, anonymous_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['num_pages'], 2)

        # test with course_id filter and integer user id
        course_id = {'course_id': unicode(self.course.id)}
        response = self.do_get('{}/{}/workgroups/?{}'.format(self.users_base_uri, test_user.id, urlencode(course_id)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)
        self.assertIsNotNone(response.data['results'][0]['name'])
        self.assertIsNotNone(response.data['results'][0]['project'])

        # test with invalid user
        response = self.do_get('{}/4356340/workgroups/'.format(self.users_base_uri))
        self.assertEqual(response.status_code, 404)

        # test with valid user but has no workgroup
        another_user_id = self._create_test_user()
        response = self.do_get('{}/{}/workgroups/'.format(self.users_base_uri, another_user_id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(len(response.data['results']), 0)

    def test_user_completions_list(self):
        user_id = self.user.id
        another_user_id = UserFactory().id
        completion_uri = '{}/{}/completions/'.format(self.courses_base_uri, unicode(self.course.id))

        for i in xrange(1, 26):
            if i > 12:
                course_user_id = another_user_id
            else:
                course_user_id = user_id
            local_content_name = 'Video_Sequence{}'.format(i)
            local_content = ItemFactory.create(
                category="videosequence",
                parent_location=self.course_content.location,
                data=str(uuid.uuid4()),
                display_name=local_content_name
            )
            completions_data = {'content_id': unicode(local_content.scope_ids.usage_id), 'user_id': course_user_id}
            response = self.do_post(completion_uri, completions_data)
            self.assertEqual(response.status_code, 201)

        # Get course module completion by user
        completion_list_uri = '{}/{}/courses/{}/completions/?page_size=6'.format(self.users_base_uri, user_id, unicode(self.course.id))
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 12)
        self.assertEqual(len(response.data['results']), 6)  # 12 matches, but only 6 per page
        self.assertEqual(response.data['results'][0]['user_id'], user_id)
        self.assertEqual(response.data['results'][0]['course_id'], unicode(self.course.id))
        self.assertEqual(response.data['num_pages'], 2)

        # Get course module completion by other user
        completion_list_uri = '{}/{}/courses/{}/completions/'.format(self.users_base_uri, another_user_id, unicode(self.course.id))
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 13)

        # Get course module completion by other user and course module id (content_id)
        content_id = {'content_id': unicode(local_content.scope_ids.usage_id)}
        completion_list_uri = '{}/{}/courses/{}/completions/?{}'.format(
            self.users_base_uri,
            course_user_id,
            unicode(self.course.id),
            urlencode(content_id)
        )
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        # Get course module completion by bogus user
        completion_list_uri = '{}/{}/courses/{}/completions/'.format(self.users_base_uri, '34323422', unicode(self.course.id))
        response = self.do_get(completion_list_uri)
        self.assertEqual(response.status_code, 404)

    def test_user_count_by_city(self):
        test_uri = self.users_base_uri

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

        response = self.do_get('{}/metrics/cities/'.format(self.users_base_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 4)
        self.assertEqual(response.data['results'][0]['city'], 'San Francisco')
        self.assertEqual(response.data['results'][0]['count'], 9)

        # filter counts by city
        response = self.do_get('{}/metrics/cities/?city=new york city'.format(self.users_base_uri))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['city'], 'New York City')
        self.assertEqual(response.data['results'][0]['count'], 6)

    def test_users_social_metrics_get_service_unavailable(self):
        test_uri = '{}/{}/courses/{}/metrics/social/'.format(self.users_base_uri, self.user.id, self.course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 500)

    def test_users_social_metrics_get_invalid_user(self):
        test_uri = '{}/12345/courses/{}/metrics/social/'.format(self.users_base_uri, self.course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @mock.patch("api_manager.users.views.get_user_social_stats", _fake_get_user_social_stats)
    def test_users_social_metrics(self):
        test_uri = '{}/{}/courses/{}/metrics/social/'.format(self.users_base_uri, self.user.id, self.course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

    @mock.patch("api_manager.users.views.get_user_social_stats", _fake_get_user_social_stats_with_end)
    def test_users_social_metrics_end_date(self):
        course = CourseFactory.create(org='TUCGLG', run='TUCGLG1', end=datetime(2012, 1, 1))

        test_uri = '{}/{}/courses/{}/metrics/social/'.format(self.users_base_uri, self.user.id, course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

    def test_users_roles_list_get(self):
        allow_access(self.course, self.user, 'staff')
        course2 = CourseFactory.create(
            display_name="TEST COURSE2",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        allow_access(course2, self.user, 'instructor')
        course3 = CourseFactory.create(
            display_name="TEST COURSE3",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        allow_access(course3, self.user, 'staff')
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)

        # filter roleset by course
        course_id = {'course_id': '{}'.format(unicode(course3.id))}
        course_filter_uri = '{}?{}'.format(test_uri, urlencode(course_id))
        response = self.do_get(course_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        # filter roleset by role
        role = {'role': 'instructor'}
        role_filter_uri = '{}?{}'.format(test_uri, urlencode(role))
        response = self.do_get(role_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        role = {'role': 'invalid_role'}
        role_filter_uri = '{}?{}'.format(test_uri, urlencode(role))
        response = self.do_get(role_filter_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

    def test_users_roles_list_get_invalid_user(self):
        test_uri = '{}/23423/roles/'.format(self.users_base_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_list_get_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        course_id = {'course_id': '{}'.format(unicode(self.test_bogus_course_id))}
        test_uri = '{}?{}'.format(test_uri, urlencode(course_id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_list_post(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        data = {'course_id': unicode(self.course.id), 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

        # Confirm this user also has forum moderation permissions
        role = Role.objects.get(course_id=self.course.id, name=FORUM_ROLE_MODERATOR)
        has_role = role.users.get(id=self.user.id)
        self.assertTrue(has_role)

    def test_users_roles_list_post_invalid_user(self):
        test_uri = '{}/2131/roles/'.format(self.users_base_uri)
        data = {'course_id': unicode(self.course.id), 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_list_post_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        data = {'course_id': self.test_bogus_course_id, 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_users_roles_list_post_invalid_role(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        data = {'course_id': unicode(self.course.id), 'role': 'invalid_role'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_users_roles_list_put(self):
        course2 = CourseFactory.create(
            display_name="TEST COURSE2",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        Role.objects.get_or_create(
            name=FORUM_ROLE_MODERATOR,
            course_id=course2.id)

        course3 = CourseFactory.create(
            display_name="TEST COURSE3",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )
        Role.objects.get_or_create(
            name=FORUM_ROLE_MODERATOR,
            course_id=course3.id)

        course4 = CourseFactory.create(
            display_name="COURSE4 NO MODERATOR",
            start=datetime(2014, 6, 16, 14, 30),
            end=datetime(2015, 1, 16, 14, 30)
        )

        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 0)

        data = {'ignore_roles': ['staff'], 'roles': [
            {'course_id': unicode(self.course.id), 'role': 'instructor'},
            {'course_id': unicode(course2.id), 'role': 'instructor'},
            {'course_id': unicode(course3.id), 'role': 'instructor'},
            {'course_id': unicode(course3.id), 'role': 'staff'},
        ]}

        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 3)
        for role in response.data['results']:
            self.assertEqual(role['role'], 'instructor')

        data = {'roles': [
            {'course_id': unicode(self.course.id), 'role': 'staff'},
            {'course_id': unicode(course2.id), 'role': 'staff'},
        ]}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)
        for role in response.data['results']:
            self.assertEqual(role['role'], 'staff')

        # Add a role that does not have a corresponding moderator role configured
        allow_access(course4, self.user, 'staff')
        # Now modify the existing no-moderator role using the API, which tries to set the moderator role
        # Also change one of the existing moderator roles, but call it using the deprecated string version
        data = {'roles': [
            {'course_id': course4.id.to_deprecated_string(), 'role': 'instructor'},
            {'course_id': course2.id.to_deprecated_string(), 'role': 'instructor'},
        ]}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 200)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 2)

    def test_users_roles_list_put_invalid_user(self):
        test_uri = '{}/2131/roles/'.format(self.users_base_uri)
        data = {'roles': [{'course_id': unicode(self.course.id), 'role': 'instructor'}]}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_list_put_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        data = {'course_id': unicode(self.course.id), 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'roles': [{'course_id': self.test_bogus_course_id, 'role': 'instructor'}]}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 400)

        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['course_id'], unicode(self.course.id))

    def test_users_roles_list_put_invalid_roles(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        data = {'roles': []}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 400)
        data = {'roles': [{'course_id': unicode(self.course.id), 'role': 'invalid-role'}]}
        response = self.do_put(test_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_users_roles_courses_detail_delete(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        data = {'course_id': unicode(self.course.id), 'role': 'instructor'}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 1)

        delete_uri = '{}instructor/courses/{}'.format(test_uri, unicode(self.course.id))
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 204)

        response = self.do_get(test_uri)
        self.assertEqual(response.data['count'], 0)

        # Confirm this user no longer has forum moderation permissions
        role = Role.objects.get(course_id=self.course.id, name=FORUM_ROLE_MODERATOR)
        try:
            has_role = role.users.get(id=self.user.id)
            self.assertTrue(False)
        except ObjectDoesNotExist:
            pass

    def test_users_roles_courses_detail_delete_invalid_course(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        delete_uri = '{}instructor/courses/{}'.format(test_uri, self.test_bogus_course_id)
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_courses_detail_delete_invalid_user(self):
        test_uri = '{}/124134/roles/'.format(self.users_base_uri)
        delete_uri = '{}instructor/courses/{}'.format(test_uri, unicode(self.course.id))
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)

    def test_users_roles_courses_detail_delete_invalid_role(self):
        test_uri = '{}/{}/roles/'.format(self.users_base_uri, self.user.id)
        delete_uri = '{}invalid_role/courses/{}'.format(test_uri, unicode(self.course.id))
        response = self.do_delete(delete_uri)
        self.assertEqual(response.status_code, 404)

    def test_mark_notification_as_read(self):
        user_id = self._create_test_user()

        msg_type = NotificationType(
            name='open-edx.edx_notifications.lib.tests.test_publisher',
            renderer='edx_notifications.renderers.basic.BasicSubjectBodyRenderer',
        )
        register_notification_type(msg_type)
        msg = NotificationMessage(
            namespace='test-runner',
            msg_type=msg_type,
            payload={
                'foo': 'bar'
            }
        )

        # now do happy path
        sent_user_msg = publish_notification_to_user(user_id, msg)

        # verify unread count
        self.assertEqual(get_notifications_count_for_user(user_id, filters={'read': False}), 1)

        # mark as read
        test_uri = '{}/{}/notifications/{}/'.format(self.users_base_uri, user_id, sent_user_msg.msg.id)
        response = self.do_post(test_uri, {"read": True})
        self.assertEqual(response.status_code, 201)

        # then verify unread count, which should be 0
        self.assertEqual(get_notifications_count_for_user(user_id, filters={'read': False}), 0)
