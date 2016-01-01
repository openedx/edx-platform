"""
Tests for organization API.
"""
import ddt
import json
import unittest

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.test import TestCase
from oauth2_provider.tests.factories import AccessTokenFactory, ClientFactory

from student.tests.factories import UserFactory
from util import organizations_helpers


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class OrganizationsAPITests(TestCase):
    """
    Tests for the organizations API endpoints.

    GET /api/organizations/v1/organization/:org_key/
    """

    def setUp(self):
        """
        Test setup for the organizations API.
        """
        super(OrganizationsAPITests, self).setUp()
        self.user_password = 'password'
        self.user = UserFactory(password=self.user_password)

        self.test_org_key = 'test_organization'
        self.test_org_url = self._generate_org_url(self.test_org_key)

    def _create_test_organization(self, org_key=None):
        """
        Helper method to create a test organization with the provide 'org_key' and
        returns the url to access it.
        """
        if org_key is None:
            org_key = self.test_org_key

        test_organization_data = {
            'name': 'Test Organization',
            'short_name': org_key,
            'description': 'Test Organization Description',
            'logo': '/test_logo.png/'
        }
        organizations_helpers.add_organization(organization_data=test_organization_data)
        return self._generate_org_url(org_key)

    def _generate_org_url(self, org_key):
        """
        Helper method to generate the url to get organization data for a
        specific organization key.
        """
        return reverse(
            'organization_api:get_organization', kwargs={'organization_key': org_key}
        )

    def test_authentication_required(self):
        """
        Verify that the endpoint requires authentication.
        """
        response = self.client.get(self.test_org_url)
        self.assertEqual(response.status_code, 401)

    def test_session_auth(self):
        """
        Verify that the endpoint supports session authentication.
        """
        self.client.login(username=self.user.username, password=self.user_password)
        response = self.client.get(self.test_org_url)
        # verify that the test org does not exist
        self.assertEqual(response.status_code, 404)

        # add a test organization
        self._create_test_organization()

        # verify that the organization api return data in correct format
        response = self.client.get(self.test_org_url)
        self.assertEqual(response.status_code, 200)
        expected_output = {
            'name': 'Test Organization',
            'short_name': 'test_organization',
            'description': 'Test Organization Description',
            'logo': 'http://testserver/test_logo.png/'
        }
        self.assertEqual(json.loads(response.content), expected_output)

    def test_oauth(self):
        """
        Verify that the organization API supports OAuth.
        """
        oauth_client = ClientFactory.create()
        access_token = AccessTokenFactory.create(user=self.user, client=oauth_client).token
        headers = {
            'HTTP_AUTHORIZATION': 'Bearer ' + access_token
        }
        response = self.client.get(self.test_org_url, **headers)
        # verify that the test org does not exist
        self.assertEqual(response.status_code, 404)

        # add a test organization
        self._create_test_organization()

        # verify that the organization api return data in correct format
        response = self.client.get(self.test_org_url, **headers)
        self.assertEqual(response.status_code, 200)
        expected_output = {
            'name': 'Test Organization',
            'short_name': 'test_organization',
            'description': 'Test Organization Description',
            'logo': 'http://testserver/test_logo.png/'
        }
        self.assertEqual(json.loads(response.content), expected_output)

    @ddt.data("test_org's", "test_org*", "test(org)", "!test", "test org")
    def test_with_invalid_org_key(self, invalid_org_key):
        """
        Verify that organization url does not match for invalid org key.
        """
        with self.assertRaises(NoReverseMatch):
            self._generate_org_url(invalid_org_key)
