"""
Unit tests for stub HTTP server base class.
"""


import json
import unittest

import requests

from common.djangoapps.terrain.stubs.http import StubHttpRequestHandler, StubHttpService, require_params


class StubHttpServiceTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()
        self.server = StubHttpService()
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.port}/set_config"

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
            'test_unicode': '\u2603 the snowman',
            'test_none': None,
            'test_boolean': False
        }

        for key, val in params.items():

            # JSON-encode each parameter
            post_params = {key: json.dumps(val)}
            response = requests.put(self.url, data=post_params)
            assert response.status_code == 200

        # Check that the expected values were set in the configuration
        for key, val in params.items():
            assert self.server.config.get(key) == val

    def test_bad_json(self):
        response = requests.put(self.url, data="{,}")
        assert response.status_code == 400

    def test_no_post_data(self):
        response = requests.put(self.url, data={})
        assert response.status_code == 200

    def test_unicode_non_json(self):
        # Send unicode without json-encoding it
        response = requests.put(self.url, data={'test_unicode': '\u2603 the snowman'})
        assert response.status_code == 400

    def test_unknown_path(self):
        response = requests.put(
            f"http://127.0.0.1:{self.server.port}/invalid_url",
            data="{}"
        )
        assert response.status_code == 404


class RequireRequestHandler(StubHttpRequestHandler):  # lint-amnesty, pylint: disable=missing-class-docstring
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
        super().setUp()
        self.server = RequireHttpService()
        self.addCleanup(self.server.shutdown)
        self.url = f"http://127.0.0.1:{self.server.port}"

    def test_require_get_param(self):

        # Expect success when we provide the required param
        response = requests.get(self.url, params={"test_param": 2})
        assert response.status_code == 200

        # Expect failure when we do not proivde the param
        response = requests.get(self.url)
        assert response.status_code == 400

        # Expect failure when we provide an empty param
        response = requests.get(self.url + "?test_param=")
        assert response.status_code == 400

    def test_require_post_param(self):

        # Expect success when we provide the required param
        response = requests.post(self.url, data={"test_param": 2})
        assert response.status_code == 200

        # Expect failure when we do not proivde the param
        response = requests.post(self.url)
        assert response.status_code == 400

        # Expect failure when we provide an empty param
        response = requests.post(self.url, data={"test_param": None})
        assert response.status_code == 400
