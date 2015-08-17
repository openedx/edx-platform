"""
Tests for Discussion API pagination support
"""
from unittest import TestCase

from django.test import RequestFactory

from discussion_api.pagination import get_paginated_data


class PaginationSerializerTest(TestCase):
    """Tests for PaginationSerializer"""
    def do_case(self, objects, page_num, num_pages, expected):
        """
        Make a dummy request, and assert that get_paginated_data with the given
        parameters returns the expected result
        """
        request = RequestFactory().get("/test")
        actual = get_paginated_data(request, objects, page_num, num_pages)
        self.assertEqual(actual, expected)

    def test_empty(self):
        self.do_case(
            [], 1, 0,
            {
                "next": None,
                "previous": None,
                "results": [],
            }
        )

    def test_only_page(self):
        self.do_case(
            ["foo"], 1, 1,
            {
                "next": None,
                "previous": None,
                "results": ["foo"],
            }
        )

    def test_first_of_many(self):
        self.do_case(
            ["foo"], 1, 3,
            {
                "next": "http://testserver/test?page=2",
                "previous": None,
                "results": ["foo"],
            }
        )

    def test_last_of_many(self):
        self.do_case(
            ["foo"], 3, 3,
            {
                "next": None,
                "previous": "http://testserver/test?page=2",
                "results": ["foo"],
            }
        )

    def test_middle_of_many(self):
        self.do_case(
            ["foo"], 2, 3,
            {
                "next": "http://testserver/test?page=3",
                "previous": "http://testserver/test?page=1",
                "results": ["foo"],
            }
        )
