import search.sorting as sorting
from django.test import TestCase

class SortingTest(TestCase):

    def test_alphabetical_sort(self):
        test_list = ["One", "Two", "3.three", "four", "Five"]
        dummy_results = [DummyResult(name, 0.0) for name in test_list]
        sorted_list = sorting.sort(dummy_results, "alphabetical")
        sorted_results = [result.data["display_name"] for result in sorted_list]
        self.assertEqual(sorted_results, ['3.three','Five', 'four', "One", 'Two'])

    def test_score_sort(self):
        test_scores = [10, 1.1, 48391023, 32.123678, 2939.3434, 0.0]
        dummy_results = [DummyResult("", score) for score in test_scores]
        sorted_list = sorting.sort(dummy_results, "relevance")
        sorted_results = [result.score for result in sorted_list]
        self.assertEqual(sorted_results, [48391023, 2939.3434, 32.123678, 10, 1.1, 0.0])
        unsorted_list = sorting.sort(dummy_results, "fake")
        self.assertEqual(test_scores, [item.score for item in unsorted_list])

class DummyResult():

    def __init__(self, display_name, score):
        self.score = score
        self.data = {"display_name": display_name}
