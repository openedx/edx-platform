# pylint: disable=E1103

"""
Run these tests @ Devstack:
    rake fasttest_lms[common/djangoapps/api_manager/tests/test_views.py]
"""
import unittest
import uuid

from django.conf import settings
from django.core.cache import cache
from django.test import TestCase, Client
from django.test.utils import override_settings

TEST_API_KEY = str(uuid.uuid4())


class SecureClient(Client):
    """ Django test client using a "secure" connection. """
    def __init__(self, *args, **kwargs):
        kwargs = kwargs.copy()
        kwargs.update({'SERVER_PORT': 443, 'wsgi.url_scheme': 'https'})
        super(SecureClient, self).__init__(*args, **kwargs)


@override_settings(EDX_API_KEY=TEST_API_KEY)
class SystemApiTests(TestCase):
    """ Test suite for base API views """

    def setUp(self):
        self.test_server_prefix = "https://testserver/api"
        self.test_username = str(uuid.uuid4())
        self.test_password = str(uuid.uuid4())
        self.test_email = str(uuid.uuid4()) + '@test.org'
        self.test_group_name = str(uuid.uuid4())

        self.client = SecureClient()
        cache.clear()

    def do_get(self, uri):
        """Submit an HTTP GET request"""
        headers = {
            'Content-Type': 'application/json',
            'X-Edx-Api-Key': str(TEST_API_KEY),
        }
        response = self.client.get(uri, headers=headers)
        return response

    def test_system_detail_get(self):
        """ Ensure the system returns base data about the system """
        test_uri = self.test_server_prefix + '/system'
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['uri'])
        self.assertGreater(len(response.data['uri']), 0)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertIsNotNone(response.data['documentation'])
        self.assertGreater(len(response.data['documentation']), 0)
        self.assertIsNotNone(response.data['name'])
        self.assertGreater(len(response.data['name']), 0)
        self.assertIsNotNone(response.data['description'])
        self.assertGreater(len(response.data['description']), 0)

    def test_system_detail_api_get(self):
        """ Ensure the system returns base data about the API """
        test_uri = self.test_server_prefix
        response = self.do_get(test_uri)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.data['uri'])
        self.assertGreater(len(response.data['uri']), 0)
        self.assertEqual(response.data['uri'], test_uri)
        self.assertGreater(len(response.data['csrf_token']), 0)
        self.assertIsNotNone(response.data['documentation'])
        self.assertGreater(len(response.data['documentation']), 0)
        self.assertIsNotNone(response.data['name'])
        self.assertGreater(len(response.data['name']), 0)
        self.assertIsNotNone(response.data['description'])
        self.assertGreater(len(response.data['description']), 0)
