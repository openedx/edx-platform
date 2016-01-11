"""
Tests for Discussion API pagination support
"""
from unittest import TestCase

from django.test import RequestFactory

from discussion_api.pagination import DiscussionAPIPagination


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

    def get_expected_response(self, results, count, num_pages, next, previous):
        """
        Generates the response dictionary with passed data
        """
        return {
            "pagination": {
                "next": next,
                "previous": previous,
                "count": count,
                "num_pages": num_pages,
            },
            "results": results
        }

    def test_empty(self):
        self.do_case(
            [], 1, 0, self.get_expected_response([], 0, 0, None, None)
        )

    def test_only_page(self):
        self.do_case(
            ["foo"], 1, 1, self.get_expected_response(["foo"], 0, 1, None, None)
        )

    def test_first_of_many(self):
        self.do_case(
            ["foo"], 1, 3, self.get_expected_response(
                ["foo"], 0, 3, "http://testserver/test?page=2", None
            )
        )

    def test_last_of_many(self):
        self.do_case(
            ["foo"], 3, 3, self.get_expected_response(
                ["foo"], 0, 3, None, "http://testserver/test?page=2"
            )
        )

    def test_middle_of_many(self):
        self.do_case(
            ["foo"], 2, 3, self.get_expected_response(
                ["foo"], 0, 3, "http://testserver/test?page=3", "http://testserver/test?page=1"
            )
        )
