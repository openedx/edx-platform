"""
Discussion API test utilities
"""
import json

import httpretty


class CommentsServiceMockMixin(object):
    """Mixin with utility methods for mocking the comments service"""
    def register_get_threads_response(self, threads, page, num_pages):
        """Register a mock response for GET on the CS thread list endpoint"""
        httpretty.register_uri(
            httpretty.GET,
            "http://localhost:4567/api/v1/threads",
            body=json.dumps({
                "collection": threads,
                "page": page,
                "num_pages": num_pages,
            }),
            status=200
        )

    def assert_last_query_params(self, expected_params):
        """
        Assert that the last mock request had the expected query parameters
        """
        actual_params = dict(httpretty.last_request().querystring)
        actual_params.pop("request_id")  # request_id is random
        self.assertEqual(actual_params, expected_params)
