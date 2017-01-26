"""
Helpers for API tests.
"""
import base64
import json

import re
from django.test import TestCase
from django.test.utils import override_settings

TEST_API_KEY = "test_api_key"


@override_settings(EDX_API_KEY=TEST_API_KEY)
class ApiTestCase(TestCase):
    """
    Parent test case for API workflow coverage
    """

    def basic_auth(self, username, password):
        """
        Returns a dictionary containing the http auth header with encoded username+password
        """
        return {'HTTP_AUTHORIZATION': 'Basic ' + base64.b64encode('%s:%s' % (username, password))}

    def request_with_auth(self, method, *args, **kwargs):
        """Issue a get request to the given URI with the API key header"""
        return getattr(self.client, method)(*args, HTTP_X_EDX_API_KEY=TEST_API_KEY, **kwargs)

    def get_json(self, *args, **kwargs):
        """Make a request with the given args and return the parsed JSON repsonse"""
        resp = self.request_with_auth("get", *args, **kwargs)
        self.assertHttpOK(resp)
        self.assertTrue(resp["Content-Type"].startswith("application/json"))
        return json.loads(resp.content)

    def assertAllowedMethods(self, uri, expected_methods):
        """Assert that the allowed methods for the given URI match the expected list"""
        resp = self.request_with_auth("options", uri)
        self.assertHttpOK(resp)
        allow_header = resp.get("Allow")
        self.assertIsNotNone(allow_header)
        allowed_methods = re.split('[^A-Z]+', allow_header)
        self.assertItemsEqual(allowed_methods, expected_methods)

    def assertSelfReferential(self, obj):
        """Assert that accessing the "url" entry in the given object returns the same object"""
        copy = self.get_json(obj["url"])
        self.assertEqual(obj, copy)

    def assertHttpOK(self, response):
        """Assert that the given response has the status code 200"""
        self.assertEqual(response.status_code, 200)

    def assertHttpForbidden(self, response):
        """Assert that the given response has the status code 403"""
        self.assertEqual(response.status_code, 403)

    def assertHttpBadRequest(self, response):
        """Assert that the given response has the status code 400"""
        self.assertEqual(response.status_code, 400)

    def assertHttpMethodNotAllowed(self, response):
        """Assert that the given response has the status code 405"""
        self.assertEqual(response.status_code, 405)

    def assertAuthDisabled(self, method, uri):
        """
        Assert that the Django rest framework does not interpret basic auth
        headers for views exposed to anonymous users as an attempt to authenticate.

        """
        # Django rest framework interprets basic auth headers
        # as an attempt to authenticate with the API.
        # We don't want this for views available to anonymous users.
        basic_auth_header = "Basic " + base64.b64encode('username:password')
        response = getattr(self.client, method)(uri, HTTP_AUTHORIZATION=basic_auth_header)
        self.assertNotEqual(response.status_code, 403)
