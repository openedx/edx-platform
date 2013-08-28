# -*- coding: utf-8 -*-

"""
This is the testing suite for the models within the search module
"""

import json
import re
from django.test import TestCase
from django.test.utils import override_settings
from pyfuzz.generator import random_regex

from search.models import SearchResults, SearchResult
from test_mongo import dummy_document

TEST_TEXT = """Lorem ipsum dolor sit amet, consectetur adipisicing elit,
            sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
            Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
            nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in
            reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
            Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia
            deserunt mollit anim id est laborum."""

TEST_GREEK = u"""Σο οι δεύτερον απόσταση απαγωγής ολόκληρο πω. Είχε γιου βάση όλα
             νου στην όπου σούκ. Ανάλυσης νεόφερτο ας εκ νεανικής τεκμήρια νε θα
             εξαιτίας δείχνουν. Τη αν ιι έν συμπαίκτης παράδειγμα υποτίθεται τελευταίες.
             Μου στίχους σαν γίνεται χιούμορ πως αρχίζει κατ σφυγμός συνθήκη. Αναγνώστη
             προτιμούν σύγχρονες τη κι να κινήματος. Φίλτρο στήθος πει ατο κεί τέλους.
             Χωρική θέσεις δε χτένας ίμερας έρευνα έμμεση αρ. Προκύψει επίλογοι ιππασίας σαν."""


def dummy_entry(score, searchable_text=None):
    """
    This creates a fully-fledged fake response entry for a given score
    """

    id_ = dummy_document("id", ["tag", "org", "course", "category", "name"], "regex", regex="[a-zA-Z0-9]", length=25)
    if searchable_text is None:
        source = dummy_document("_source", ["thumbnail", "searchable_text"], "regex", regex="[a-zA-Z0-9]", length=50)
    else:
        source = dummy_document("_source", ["thumbnail"], "regex", regex="[a-zA-Z0-9]", length=50)
        source["_source"].update({"searchable_text": searchable_text})
    string_id = json.dumps(id_["id"])
    source["_source"].update({"id": string_id, "course_id": random_regex(regex="[a-zA-Z0-9/]", length=50)})
    document = {"_score": score}
    source.update(document)
    return source


class FakeResponse(object):
    """
    Fake minimal response, just wrapping a given dictionary in a response-like object
    """

    def __init__(self, dictionary):
        self.content = json.dumps(dictionary)


@override_settings(SENTENCE_TOKENIZER="tokenizers/punkt/english.pickle")
@override_settings(STEMMER="ENGLISH")
class ModelTest(TestCase):
    """
    Tests SearchResults and SearchResult models as well as associated helper functions
    """

    def test_search_result_init(self):
        check = SearchResult(dummy_entry(1.0), ["fake-query"])
        self.assertTrue(bool(re.match(r"^[a-zA-Z0-9]+$", check.snippets)))
        self.assertTrue(check.url.startswith("/courses"))
        self.assertTrue("/jump_to/" in check.url)
        self.assertEqual(check.category, json.loads(check.data["id"])["category"])

    def test_snippet_generation(self):
        document = dummy_entry(1.0, TEST_TEXT)
        result = SearchResult(document, [u"quis nostrud"])
        self.assertTrue(result.snippets.startswith("Ut enim ad minim"))
        self.assertTrue(result.snippets.strip().endswith("anim id est laborum."))
        self.assertTrue('<b class="highlight">quis</b>' in result.snippets)
        self.assertTrue('<b class="highlight">nostrud</b>' in result.snippets)

    @override_settings(SENTENCE_TOKENIZER="DETECT")
    @override_settings(STEMMER="DETECT")
    def test_language_detection(self):
        document = dummy_entry(1.0, TEST_GREEK)
        result = SearchResult(document, [u"νου στην όπου"])
        self.assertTrue(result.snippets.startswith(u"Είχε γιου"))

    def test_search_results(self):
        scores = [1.0, 5.2, 2.0, 123.2]
        hits = [dummy_entry(score) for score in scores]
        full_return = FakeResponse({"hits": {"hits": hits}})
        results = SearchResults(full_return, s=["fake query"], sort="relevance")
        self.assertTrue(all([isinstance(result, SearchResult) for result in results.entries]))
        self.assertEqual(["fake query"], results.query)
        scores = [entry.score for entry in results.entries]
        self.assertEqual([123.2, 5.2, 2.0, 1.0], scores)

    def test_get_content_url(self):
        document = dummy_entry(1.0)
        id_ = json.dumps({
            "org": "test-org",
            "course": "test-course",
            "category": "fake-category",
            "tag": "fake-tag",
            "name": "fake-name"
        })
        document["_source"]["id"] = id_
        document["_source"]['thumbnail'] = "/static/images/test/image/url.jpg"
        result = SearchResult(document, "fake query")
        expected_content_url = "/c4x/test-org/test-course/asset/images_test_image_url.jpg"
        self.assertEqual(expected_content_url, result.thumbnail)
