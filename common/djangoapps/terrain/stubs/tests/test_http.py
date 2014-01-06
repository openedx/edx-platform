"""
Unit tests for stub HTTP server base class.
"""

import unittest
import requests
import json
from terrain.stubs.http import StubHttpService


class StubHttpServiceTest(unittest.TestCase):

    def setUp(self):
        self.server = StubHttpService()
        self.addCleanup(self.server.shutdown)

    def test_configure(self):
        """
        All HTTP stub servers have an end-point that allows
        clients to configure how the server responds.
        """
        params = {
            'test_str': 'This is only a test',
            'test_int': 12345,
            'test_float': 123.45,
            'test_unicode': u'\u2603 the snowman',
            'test_dict': { 'test_key': 'test_val' }
        }

        for key, val in params.iteritems():
            post_params = {key: json.dumps(val)}
            response = requests.put(
                "http://127.0.0.1:{0}/set_config".format(self.server.port),
                data=post_params
            )

            self.assertEqual(response.status_code, 200)

        # Check that the expected values were set in the configuration
        for key, val in params.iteritems():
            self.assertEqual(self.server.config(key), val)

    def test_default_config(self):
        self.assertEqual(self.server.config('not_set', default=42), 42)

    def test_bad_json(self):
        response = requests.put(
            "http://127.0.0.1:{0}/set_config".format(self.server.port),
            data="{,}"
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_path(self):
        response = requests.put(
            "http://127.0.0.1:{0}/invalid_url".format(self.server.port),
            data="{}"
        )
        self.assertEqual(response.status_code, 404)
