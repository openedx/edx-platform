"""
Unit tests for stub HTTP server base class.
"""


import json
import unittest

import requests
import six

from common.djangoapps.terrain.stubs.http import StubHttpRequestHandler, StubHttpService, require_params


class StubHttpServiceTest(unittest.TestCase):

    def setUp(self):
        super(StubHttpServiceTest, self).setUp()
        self.server = StubHttpService()
        self.addCleanup(self.server.shutdown)
        self.url = "http://127.0.0.1:{0}/set_config".format(self.server.port)

    def test_configure(self):
        """
        All HTTP stub servers have an end-point that allows
        clients to configure how the server responds.
        """
        params = {
            'test_str': 'This is only a test',
            'test_empty': '',
            'test_int': 12345,
            'test_float': 123.45,
            'test_dict': {
                'test_key': 'test_val',
            },
            'test_empty_dict': {},
            'test_unicode': u'\u2603 the snowman',
            'test_none': None,
            'test_boolean': False
        }

        for key, val in six.iteritems(params):

            # JSON-encode each parameter
            post_params = {key: json.dumps(val)}
            response = requests.put(self.url, data=post_params)
            self.assertEqual(response.status_code, 200)

        # Check that the expected values were set in the configuration
        for key, val in six.iteritems(params):
            self.assertEqual(self.server.config.get(key), val)

    def test_bad_json(self):
        response = requests.put(self.url, data="{,}")
        self.assertEqual(response.status_code, 400)

    def test_no_post_data(self):
        response = requests.put(self.url, data={})
        self.assertEqual(response.status_code, 200)

    def test_unicode_non_json(self):
        # Send unicode without json-encoding it
        response = requests.put(self.url, data={'test_unicode': u'\u2603 the snowman'})
        self.assertEqual(response.status_code, 400)

    def test_unknown_path(self):
        response = requests.put(
            "http://127.0.0.1:{0}/invalid_url".format(self.server.port),
            data="{}"
        )
        self.assertEqual(response.status_code, 404)


class RequireRequestHandler(StubHttpRequestHandler):
    @require_params('GET', 'test_param')
    def do_GET(self):
        self.send_response(200)

    @require_params('POST', 'test_param')
    def do_POST(self):
        self.send_response(200)


class RequireHttpService(StubHttpService):
    HANDLER_CLASS = RequireRequestHandler


class RequireParamTest(unittest.TestCase):
    """
    Test the decorator for requiring parameters.
    """

    def setUp(self):
        super(RequireParamTest, self).setUp()
        self.server = RequireHttpService()
        self.addCleanup(self.server.shutdown)
        self.url = "http://127.0.0.1:{port}".format(port=self.server.port)

    def test_require_get_param(self):

        # Expect success when we provide the required param
        response = requests.get(self.url, params={"test_param": 2})
        self.assertEqual(response.status_code, 200)

        # Expect failure when we do not proivde the param
        response = requests.get(self.url)
        self.assertEqual(response.status_code, 400)

        # Expect failure when we provide an empty param
        response = requests.get(self.url + "?test_param=")
        self.assertEqual(response.status_code, 400)

    def test_require_post_param(self):

        # Expect success when we provide the required param
        response = requests.post(self.url, data={"test_param": 2})
        self.assertEqual(response.status_code, 200)

        # Expect failure when we do not proivde the param
        response = requests.post(self.url)
        self.assertEqual(response.status_code, 400)

        # Expect failure when we provide an empty param
        response = requests.post(self.url, data={"test_param": None})
        self.assertEqual(response.status_code, 400)
