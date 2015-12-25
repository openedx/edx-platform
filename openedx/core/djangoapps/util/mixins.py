"""Mixins for use during testing."""
import json

import httpretty


class MockApiMixin(object):
    """
    Mixin mocking API URLs and providing fake data for testing.
    """
    def mock_api(self, url, data, status_code=200, reset_uri=True):
        """Utility for mocking out API URLs."""
        self.assertTrue(httpretty.is_enabled(), msg='httpretty must be enabled to mock Programs API calls.')

        body = json.dumps(data)
        if reset_uri:
            httpretty.reset()

        httpretty.register_uri(httpretty.GET, url, body=body, content_type='application/json', status=status_code)
