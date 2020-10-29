"""
Tests for Discussion API pagination support
"""


from unittest import TestCase

from django.test import RequestFactory

from lms.djangoapps.discussion.rest_api.pagination import DiscussionAPIPagination
from lms.djangoapps.discussion.rest_api.tests.utils import make_paginated_api_response


class PaginationSerializerTest(TestCase):
    """Tests for PaginationSerializer"""

    def do_case(self, objects, page_num, num_pages, expected):
        """
        Make a dummy request, and assert that get_paginated_data with the given
        parameters returns the expected result
        """
        request = RequestFactory().get("/test")
        paginator = DiscussionAPIPagination(request, page_num, num_pages)
        actual = paginator.get_paginated_response(objects)
        self.assertEqual(actual.data, expected)

    def test_empty(self):
        self.do_case(
            [], 1, 0, make_paginated_api_response(
                results=[], count=0, num_pages=0, next_link=None, previous_link=None
            )
        )

    def test_only_page(self):
        self.do_case(
            ["foo"], 1, 1, make_paginated_api_response(
                results=["foo"], count=0, num_pages=1, next_link=None, previous_link=None
            )
        )

    def test_first_of_many(self):
        self.do_case(
            ["foo"], 1, 3, make_paginated_api_response(
                results=["foo"], count=0, num_pages=3, next_link="http://testserver/test?page=2", previous_link=None
            )
        )

    def test_last_of_many(self):
        self.do_case(
            ["foo"], 3, 3, make_paginated_api_response(
                results=["foo"], count=0, num_pages=3, next_link=None, previous_link="http://testserver/test?page=2"
            )
        )

    def test_middle_of_many(self):
        self.do_case(
            ["foo"], 2, 3, make_paginated_api_response(
                results=["foo"],
                count=0,
                num_pages=3,
                next_link="http://testserver/test?page=3",
                previous_link="http://testserver/test?page=1"
            )
        )
