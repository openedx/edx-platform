"""
Test suite for various sorting methods in sorting.sort
"""

from django.test import TestCase
from pyfuzz.generator import random_item

import search.sorting as sorting


class SortingTest(TestCase):
    """
    This contains all of the current sorting tests.
    """

    def test_alphabetical_sort(self):
        test_list = ["One", "Two", "3.three", "four", "Five"]
        dummy_results = [DummyResult(name, i) for i, name in enumerate(test_list)]
        sorted_list = sorting.sort(dummy_results, "alphabetical")
        sorted_results = [result.data["display_name"] for result in sorted_list]
        self.assertEqual(sorted_results, ['3.three', 'Five', 'four', "One", 'Two'])

    def test_score_sort(self):
        test_scores = [10, 1.1, 48391023, 32.123678, 2939.3434, 0.0]
        dummy_results = [DummyResult(random_item("ascii", length=20), score) for score in test_scores]
        sorted_list = sorting.sort(dummy_results, "relevance")
        sorted_results = [result.score for result in sorted_list]
        self.assertEqual(sorted_results, [48391023, 2939.3434, 32.123678, 10, 1.1, 0.0])
        unsorted_list = sorting.sort(dummy_results, "fake")
        self.assertEqual(test_scores, [item.score for item in unsorted_list])


class DummyResult():
    """
    This generates a minimal fake result to test current active sort methods
    """

    def __init__(self, display_name, score):
        self.score = score
        self.data = {"display_name": display_name}
