# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_group_views.py]
"""
from random import randint
import uuid
import json

from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from api_manager.models import GroupRelationship, GroupProfile
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
class GroupsApiTests(ModuleStoreTestCase):
    """ Test suite for Groups API views """

    def setUp(self):
        self.test_server_prefix = 'https://testserver'
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_group_name = str(uuid.uuid4())
        self.base_users_uri = '/api/users'
        self.base_groups_uri = '/api/groups'

        self.course = CourseFactory.create()
        self.test_course_id = self.course.id

        self.client = SecureClient()
        cache.clear()

    def do_post(self, uri, data):
        """Submit an HTTP POST request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.post(uri, headers=headers, data=json.dumps(data), content_type='application/json')
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

    def test_group_list_post(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        confirm_uri = self.test_server_prefix + self.base_groups_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertGreater(len(response.data['name']), 0)

    def test_group_list_get_with_profile(self):
        group_type = 'series'
        profile_data = {'display_name': 'My first series'}
        data = {
            'name': self.test_group_name,
            'type': group_type,
            'data': profile_data
        }
        response = self.do_post(self.base_groups_uri, data)
        self.assertGreater(response.data['id'], 0)
        group_id = response.data['id']

        # query for list of groups, but don't put the type filter
        test_uri = self.base_groups_uri
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 400)

        # try again with filter
        test_uri = '{}?type={}'.format(self.base_groups_uri, group_type)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], group_id)
        self.assertEqual(response.data[0]['type'], 'series')
        self.assertEqual(response.data[0]['name'], self.test_group_name)
        response_profile_data = response.data[0]['data']
        self.assertEqual(response_profile_data['display_name'], 'My first series')

        # query the group detail
        test_uri = '{}/{}'.format(self.base_groups_uri, str(group_id))
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], group_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['name'], self.test_group_name)
        self.assertEqual(response.data['type'], 'series')
        response_profile_data = response.data['data']
        self.assertEqual(response_profile_data['display_name'], 'My first series')

        # update the profile
        profile_data = {'display_name': 'My updated series'}
        data = {
            'name': self.test_group_name,
            'type': 'seriesX',
            'data': profile_data
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)

        # requery the filter
        test_uri = self.base_groups_uri + '?type=series'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

        test_uri = self.base_groups_uri + '?type=seriesX'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], group_id)
        self.assertEqual(response.data[0]['type'], 'seriesX')
        self.assertEqual(response.data[0]['name'], self.test_group_name)
        response_profile_data = response.data[0]['data']
        self.assertEqual(response_profile_data['display_name'], 'My updated series')

    def test_group_list_post_invalid_name(self):
        data = {'name': '', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_group_list_post_missing_type(self):
        data = {'name': ''}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 400)

    def test_group_list_get_uses_base_group_name(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        profile = GroupProfile.objects.get(group_id=group_id)
        profile.name = ''
        profile.save()
        test_uri = '{}?type=test'.format(self.base_groups_uri)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], '{:04d}: {}'.format(group_id, self.test_group_name))
        profile.name = None
        profile.save()
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]['name'], '{:04d}: {}'.format(group_id, self.test_group_name))

    def test_group_detail_get(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], group_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['name'], self.test_group_name)

    def test_group_detail_get_uses_base_group_name(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        group_id = response.data['id']
        profile = GroupProfile.objects.get(group_id=group_id)
        profile.name = ''
        profile.save()
        test_uri = self.base_groups_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], group_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['name'], '{:04d}: {}'.format(group_id, self.test_group_name))

    def test_group_detail_get_with_missing_profile(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(response.data['id'], 0)
        group_id = response.data['id']
        GroupProfile.objects.get(group_id=group_id).delete()
        test_uri = self.base_groups_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], group_id)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['name'], '{:04d}: {}'.format(group_id, self.test_group_name))

    def test_group_detail_get_undefined(self):
        test_uri = self.base_groups_uri + '/123456789'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_detail_post(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = response.data['uri']
        self.assertEqual(response.status_code, 201)
        group_type = 'seriesX'
        data = {
            'name': self.test_group_name,
            'type': group_type,
            'data': {
                'display_name': 'My updated series'
            }
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['id'], group_id)
        self.assertEqual(response.data['name'], self.test_group_name)
        self.assertEqual(response.data['uri'], test_uri)

    def test_group_detail_post_invalid_group(self):
        test_uri = '{}/23209232'.format(self.base_groups_uri)
        group_type = 'seriesX'
        data = {
            'name': self.test_group_name,
            'type': group_type,
            'data': {
                'display_name': 'My updated series'
            }
        }
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_users_list_post(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email,
            'username': local_username,
            'password': self.test_password,
            'first_name': 'Joe',
            'last_name': 'Smith'
        }
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = self.test_server_prefix + test_uri + '/' + str(response.data['user_id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['user_id'], str(user_id))

    def test_group_users_list_post_duplicate(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    def test_group_users_list_post_invalid_group(self):
        test_uri = self.base_groups_uri + '/1239878976'
        test_uri = test_uri + '/users'
        data = {'user_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_users_list_post_invalid_user(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = '{}/{}/users'.format(self.base_groups_uri, str(response.data['id']))
        data = {'user_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_users_list_get(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {
            'email': self.test_email,
            'username': local_username,
            'password': self.test_password,
            'first_name': 'Joe',
            'last_name': 'Smith'
        }
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(group_id)
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        users = response.data['users']
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0]['id'], user_id)
        self.assertEqual(users[0]['username'], local_username)
        self.assertEqual(users[0]['email'], self.test_email)
        self.assertEqual(users[0]['first_name'], 'Joe')
        self.assertEqual(users[0]['last_name'], 'Smith')

    def test_group_users_list_get_invalid_group(self):
        test_uri = self.base_groups_uri + '/1231241/users'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_users_detail_get(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.test_server_prefix + test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertEqual(response.data['user_id'], user_id)

    def test_group_users_detail_delete(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        test_uri = test_uri + '/' + str(user_id)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)  # Idempotent
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_users_detail_delete_invalid_group(self):
        test_uri = self.base_groups_uri + '/123987102/users/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_group_users_detail_delete_invalid_user(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        test_uri = test_uri + '/users/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_group_users_detail_get_undefined(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group', 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(group_id) + '/users/' + str(user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_list_post_hierarchical(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = delta_response.data['id']
        relationship_type = 'h'  # Hierarchical
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri + '/' + str(response.data['group_id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['relationship_type'], relationship_type)

    def test_group_groups_list_post_linked(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = delta_response.data['id']
        relationship_type = 'g'  # Graph
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri + '/' + str(response.data['group_id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['relationship_type'], relationship_type)

    def test_group_groups_list_post_linked_duplicate(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = delta_response.data['id']
        relationship_type = 'g'  # Graph
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        # Duplicate responses are idemnotent in this case
        self.assertEqual(response.status_code, 201)

    def test_group_groups_list_post_invalid_group(self):
        test_uri = self.base_groups_uri + '/123098/groups'
        relationship_type = 'g'  # Graph
        data = {'group_id': '232987', 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_list_post_invalid_relationship_type(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = delta_response.data['id']
        relationship_type = "z"  # Graph
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 406)

    def test_group_groups_list_get(self):
        data = {'name': 'Bravo Group', 'type': 'test'}
        bravo_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(bravo_response.status_code, 201)
        bravo_group_id = bravo_response.data['id']
        bravo_groups_uri = bravo_response.data['uri'] + '/groups'

        data = {'name': 'Charlie Group', 'type': 'test'}
        charlie_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(charlie_response.status_code, 201)
        charlie_group_id = charlie_response.data['id']
        relationship_type = 'h'  # Hierarchical
        data = {'group_id': charlie_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Foxtrot Group', 'type': 'test'}
        foxtrot_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(foxtrot_response.status_code, 201)
        foxtrot_group_id = foxtrot_response.data['id']
        relationship_type = 'g'  # Graph
        data = {'group_id': foxtrot_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Tango Group', 'type': 'test'}
        tango_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(tango_response.status_code, 201)
        tango_group_id = tango_response.data['id']
        tango_uri = tango_response.data['uri']
        data = {'group_id': bravo_group_id, 'relationship_type': relationship_type}
        tango_groups_uri = tango_uri + '/groups'
        response = self.do_post(tango_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(bravo_groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        group_idlist = (charlie_group_id, foxtrot_group_id, tango_group_id)
        relationship_count = 0
        for relationship in response.data:
            relationship_count = relationship_count + 1
            group_id = relationship['id']
            self.assertGreater(group_id, 0)
            self.assertFalse(bravo_group_id == group_id)
            self.assertTrue(relationship['relationship_type'] in ["h", "g"])
            self.assertGreater(len(relationship['uri']), 0)
        self.assertEqual(relationship_count, len(group_idlist))

    def test_group_groups_list_get_with_profile_type(self):
        data = {'name': 'Bravo Group', 'type': 'test'}
        bravo_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(bravo_response.status_code, 201)
        bravo_group_id = bravo_response.data['id']
        bravo_groups_uri = bravo_response.data['uri'] + '/groups?type=test_group'

        data = {'name': 'Charlie Group', 'type': 'test_group'}
        charlie_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(charlie_response.status_code, 201)
        charlie_group_id = charlie_response.data['id']
        relationship_type = 'h'  # Hierarchical
        data = {'group_id': charlie_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Foxtrot Group', 'type': 'test_group'}
        foxtrot_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(foxtrot_response.status_code, 201)
        foxtrot_group_id = foxtrot_response.data['id']
        relationship_type = 'g'  # Graph
        data = {'group_id': foxtrot_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Tango Group', 'type': 'test'}
        tango_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(tango_response.status_code, 201)
        tango_uri = tango_response.data['uri']
        data = {'group_id': bravo_group_id, 'relationship_type': relationship_type}
        tango_groups_uri = tango_uri + '/groups'
        response = self.do_post(tango_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        response = self.do_get(bravo_groups_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)
        group_idlist = (charlie_group_id, foxtrot_group_id)
        relationship_count = 0
        for relationship in response.data:
            relationship_count = relationship_count + 1
            group_id = relationship['id']
            self.assertGreater(group_id, 0)
            self.assertFalse(bravo_group_id == group_id)
            self.assertTrue(relationship['relationship_type'] in ["h", "g"])
            self.assertGreater(len(relationship['uri']), 0)
        self.assertEqual(relationship_count, len(group_idlist))

    def test_group_groups_list_get_notfound(self):
        test_uri = self.base_groups_uri + '/213213123/groups'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_detail_get_hierarchical(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        alpha_group_id = alpha_response.data['id']
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        delta_group_id = delta_response.data['id']
        relationship_type = 'h'  # Hierarchical
        data = {'group_id': delta_group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri']
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['from_group_id'], str(alpha_group_id))
        self.assertEqual(response.data['to_group_id'], str(delta_group_id))
        self.assertEqual(response.data['relationship_type'], relationship_type)

    def test_group_groups_detail_get_linked(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        alpha_group_id = alpha_response.data['id']
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        delta_group_id = delta_response.data['id']
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        relationship_type = 'g'  # Graph
        data = {'group_id': delta_group_id, 'relationship_type': relationship_type}
        delta_group = GroupRelationship.objects.get(group_id=delta_group_id)
        delta_group.parent_group_id = None
        delta_group.save()
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri']
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['from_group_id'], str(alpha_group_id))
        self.assertEqual(response.data['to_group_id'], str(delta_group_id))
        self.assertEqual(response.data['relationship_type'], relationship_type)

    def test_group_groups_detail_get_notfound(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups/gaois89sdf98'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_detail_delete_hierarchical(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        data = {'name': 'Gamma Group', 'type': 'test'}
        gamma_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(gamma_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = gamma_response.data['id']
        relationship_type = 'h'
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri']
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        try:
            self.assertIsNone(response.data['message'])
        except KeyError:
            pass
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_detail_delete_linked(self):
        data = {'name': 'Alpha Group', 'type': 'test'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group', 'type': 'test'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group', 'type': 'test'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        data = {'name': 'Gamma Group', 'type': 'test'}
        gamma_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(gamma_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = gamma_response.data['id']
        relationship_type = 'g'
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri']
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        try:
            self.assertIsNone(response.data['message'])
        except KeyError:
            pass
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_groups_detail_delete_invalid(self):
        test_uri = self.base_groups_uri + '/1231234232/groups/1'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_courses_list_post(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': self.test_course_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = test_uri + '/' + self.course.id
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['course_id'], self.test_course_id)

    def test_group_courses_list_post_duplicate(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': self.test_course_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    def test_group_courses_list_post_invalid_group(self):
        test_uri = self.base_groups_uri + '/1239878976/courses'
        data = {'course_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_courses_list_post_invalid_course(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': "987/23/896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    def test_group_courses_list_get(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': self.test_course_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        confirm_uri = test_uri + '/' + self.course.id
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertEqual(response.data['course_id'], self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['course_id'], self.test_course_id)
        self.assertEqual(response.data[0]['display_name'], self.course.display_name)

    def test_group_courses_list_get_invalid_group(self):
        test_uri = self.base_groups_uri + '/1231241/courses'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_courses_detail_get(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        group_id = response.data['id']
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': self.test_course_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}/{}/courses/{}'.format(self.base_groups_uri, group_id, self.test_course_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        confirm_uri = '{}{}/{}/courses/{}'.format(
            self.test_server_prefix,
            self.base_groups_uri,
            group_id,
            self.test_course_id
        )
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertEqual(response.data['course_id'], self.test_course_id)

    def test_group_courses_detail_delete(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri'] + '/courses'
        data = {'course_id': self.test_course_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri']
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)  # Idempotent
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    def test_group_courses_detail_delete_invalid_group(self):
        test_uri = self.base_groups_uri + '/123987102/courses/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_group_courses_detail_delete_invalid_course(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = response.data['uri'] + '/courses/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    def test_group_courses_detail_get_undefined(self):
        data = {'name': self.test_group_name, 'type': 'test'}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        test_uri = '{}/courses/{}'.format(response.data['uri'], self.course.id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)
