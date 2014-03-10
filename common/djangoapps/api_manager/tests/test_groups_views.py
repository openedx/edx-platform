# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_group_views.py]
"""
from random import randint
import unittest
import uuid

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

from api_manager.models import GroupRelationship

TEST_API_KEY = str(uuid.uuid4())


@override_settings(EDX_API_KEY=TEST_API_KEY)
class GroupsApiTests(TestCase):
    """ Test suite for Groups API views """

    def setUp(self):
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_group_name = str(uuid.uuid4())
        self.base_users_uri = '/api/users'
        self.base_groups_uri = '/api/groups'

        self.client = Client()
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_list_post(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['id'])
        self.assertGreater(response.data['id'], 0)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.base_groups_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['name'])
        self.assertGreater(len(response.data['name']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_list_post_duplicate(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertIsNotNone(response.data['id'])
        self.assertGreater(response.data['id'], 0)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = self.base_groups_uri + '/' + str(response.data['id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['name'])
        self.assertGreater(len(response.data['name']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_detail_get(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['id'])
        self.assertGreater(response.data['id'], 0)
        self.assertIsNotNone(response.data['uri'])
        self.assertGreater(len(response.data['uri']), 0)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['name'])
        self.assertGreater(len(response.data['name']), 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_detail_get_undefined(self):
        test_uri = self.base_groups_uri + '/123456789'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_list_post(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data['uri']), 0)
        confirm_uri = test_uri + '/' + str(response.data['user_id'])
        self.assertEqual(response.data['uri'], confirm_uri)
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertIsNotNone(response.data['user_id'])
        self.assertGreater(response.data['user_id'], 0)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_list_post_duplicate(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group'}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        response = self.do_get(test_uri)
        test_uri = test_uri + '/users'
        data = {'user_id': user_id}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 201)
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 409)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_list_post_invalid_resources(self):
        test_uri = self.base_groups_uri + '/1239878976'
        test_uri = test_uri + '/users'
        data = {'user_id': "98723896"}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_detail_get(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group'}
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
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertEqual(response.data['group_id'], group_id)
        self.assertIsNotNone(response.data['user_id'])
        self.assertGreater(response.data['user_id'], 0)
        self.assertEqual(response.data['user_id'], user_id)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_detail_delete(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group'}
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_detail_delete_invalid_group(self):
        test_uri = self.base_groups_uri + '/123987102/users/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_detail_delete_invalid_user(self):
        data = {'name': self.test_group_name}
        response = self.do_post(self.base_groups_uri, data)
        test_uri = self.base_groups_uri + '/' + str(response.data['id'])
        test_uri = test_uri + '/users/123124'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 204)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_users_detail_get_undefined(self):
        local_username = self.test_username + str(randint(11, 99))
        data = {'email': self.test_email, 'username': local_username, 'password': self.test_password}
        response = self.do_post(self.base_users_uri, data)
        user_id = response.data['id']
        data = {'name': 'Alpha Group'}
        response = self.do_post(self.base_groups_uri, data)
        group_id = response.data['id']
        test_uri = self.base_groups_uri + '/' + str(group_id) + '/users/' + str(user_id)
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_post_hierarchical(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
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
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertIsNotNone(response.data['relationship_type'])
        self.assertGreater(len(response.data['relationship_type']), 0)
        self.assertEqual(response.data['relationship_type'], relationship_type)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_post_linked(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
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
        self.assertIsNotNone(response.data['group_id'])
        self.assertGreater(response.data['group_id'], 0)
        self.assertEqual(response.data['group_id'], str(group_id))
        self.assertIsNotNone(response.data['relationship_type'])
        self.assertGreater(len(response.data['relationship_type']), 0)
        self.assertEqual(response.data['relationship_type'], relationship_type)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_post_linked_duplicate(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_post_invalid_group(self):
        test_uri = self.base_groups_uri + '/123098/groups'
        relationship_type = 'g'  # Graph
        data = {'group_id': '232987', 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_post_invalid_relationship_type(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups'
        group_id = delta_response.data['id']
        relationship_type = "z"  # Graph
        data = {'group_id': group_id, 'relationship_type': relationship_type}
        response = self.do_post(test_uri, data)
        self.assertEqual(response.status_code, 406)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_get(self):
        data = {'name': 'Bravo Group'}
        bravo_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(bravo_response.status_code, 201)
        bravo_group_id = bravo_response.data['id']
        bravo_groups_uri = bravo_response.data['uri'] + '/groups'

        data = {'name': 'Charlie Group'}
        charlie_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(charlie_response.status_code, 201)
        charlie_group_id = charlie_response.data['id']
        relationship_type = 'h'  # Hierarchical
        data = {'group_id': charlie_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Foxtrot Group'}
        foxtrot_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(foxtrot_response.status_code, 201)
        foxtrot_group_id = foxtrot_response.data['id']
        relationship_type = 'g'  # Graph
        data = {'group_id': foxtrot_group_id, 'relationship_type': relationship_type}
        response = self.do_post(bravo_groups_uri, data)
        self.assertEqual(response.status_code, 201)

        data = {'name': 'Tango Group'}
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_list_get_notfound(self):
        test_uri = self.base_groups_uri + '/213213123/groups'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_get_hierarchical(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        alpha_group_id = alpha_response.data['id']
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
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
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['from_group_id'])
        self.assertGreater(response.data['from_group_id'], 0)
        self.assertEqual(response.data['from_group_id'], str(alpha_group_id))
        self.assertIsNotNone(response.data['to_group_id'])
        self.assertGreater(response.data['to_group_id'], 0)
        self.assertEqual(response.data['to_group_id'], str(delta_group_id))
        self.assertIsNotNone(response.data['relationship_type'])
        self.assertGreater(len(response.data['relationship_type']), 0)
        self.assertEqual(response.data['relationship_type'], relationship_type)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_get_linked(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        alpha_group_id = alpha_response.data['id']
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
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
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['from_group_id'])
        self.assertGreater(response.data['from_group_id'], 0)
        self.assertEqual(response.data['from_group_id'], str(alpha_group_id))
        self.assertIsNotNone(response.data['to_group_id'])
        self.assertGreater(response.data['to_group_id'], 0)
        self.assertEqual(response.data['to_group_id'], str(delta_group_id))
        self.assertIsNotNone(response.data['relationship_type'])
        self.assertGreater(len(response.data['relationship_type']), 0)
        self.assertEqual(response.data['relationship_type'], relationship_type)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_get_notfound(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        test_uri = alpha_response.data['uri'] + '/groups/gaois89sdf98'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 404)

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_delete_hierarchical(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        data = {'name': 'Gamma Group'}
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_delete_linked(self):
        data = {'name': 'Alpha Group'}
        alpha_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(alpha_response.status_code, 201)
        data = {'name': 'Beta Group'}
        beta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(beta_response.status_code, 201)
        data = {'name': 'Delta Group'}
        delta_response = self.do_post(self.base_groups_uri, data)
        self.assertEqual(delta_response.status_code, 201)
        data = {'name': 'Gamma Group'}
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

    @unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
    def test_group_groups_detail_delete_invalid(self):
        test_uri = self.base_groups_uri + '/1231234232/groups/1'
        response = self.do_delete(test_uri)
        self.assertEqual(response.status_code, 404)
