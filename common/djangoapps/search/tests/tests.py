from django.test import TestCase
from django.test.utils import override_settings
from elasticsearch import Elasticsearch
# from nose.tools import set_trace

from search.manager import SearchEngine
from search.elastic import ElasticSearchEngine

from .mock_search_engine import MockSearchEngine

TEST_INDEX_NAME = "test_index"

# We override ElasticSearchEngine class in order to force an index refresh upon index
# otherwise we often get results from the prior state, rendering the tests less useful


class ForceRefreshElasticSearchEngine(ElasticSearchEngine):

    def index(self, doc_type, body, **kwargs):
        kwargs.update({
            "refresh": True
        })
        super(ForceRefreshElasticSearchEngine, self).index(doc_type, body, **kwargs)

TEST_ENGINE = MockSearchEngine
# Uncomment below in order to test against Elastic Search installation
# TEST_ENGINE = ForceRefreshElasticSearchEngine


@override_settings(SEARCH_ENGINE=TEST_ENGINE)
class ElasticSearchTests(TestCase):

    _searcher = None

    @property
    def searcher(self):
        if self._searcher is None:
            self._searcher = SearchEngine.get_search_engine(TEST_INDEX_NAME)
        return self._searcher

    @property
    def _is_elastic(self):
        return isinstance(self.searcher, ElasticSearchEngine)

    def setUp(self):
        if self._is_elastic:
            es = Elasticsearch()
            # Make sure that we are fresh
            es.indices.delete(index=TEST_INDEX_NAME, ignore=[400, 404])

            config_body = {}
            es.indices.create(index=TEST_INDEX_NAME, ignore=400, body=config_body)
        else:
            self._searcher = None

    def tearDown(self):
        if self._is_elastic:
            es = Elasticsearch()
            es.indices.delete(index=TEST_INDEX_NAME, ignore=[400, 404])
        else:
            self._searcher = None

    def test_factory_creator(self):
        self.assertTrue(isinstance(self.searcher, SearchEngine))

    def test_find_all(self):
        test_string = "A test string"
        self.searcher.index("test_doc", {"name": test_string})

        # search everything
        response = self.searcher.search(None)
        self.assertEqual(response["total"], 1)
        results = response["results"]
        self.assertEqual(results[0]["data"]["name"], test_string)

        self.searcher.index("not_test_doc", {"value": test_string})

        response = self.searcher.search(None)
        self.assertEqual(response["total"], 2)
        results = response["results"]
        test_0 = results[0]["data"] if "name" in results[0]["data"] else results[1]["data"]
        test_1 = results[1]["data"] if "name" in results[0]["data"] else results[0]["data"]
        self.assertEqual(test_0["name"], test_string)
        self.assertEqual(test_1["value"], test_string)

    def test_find_doctype(self):
        test_string = "A test string"
        self.searcher.index("test_doc", {"name": test_string})

        # search by doc_type
        response = self.searcher.search(None, doc_type="test_doc")
        self.assertEqual(response["total"], 1)

        response = self.searcher.search(None, doc_type="not_test_doc")
        self.assertEqual(response["total"], 0)

        self.searcher.index("not_test_doc", {"value": test_string})

        response = self.searcher.search(None, doc_type="not_test_doc")
        self.assertEqual(response["total"], 1)

    def test_find_string(self):
        test_string = "A test string"
        self.searcher.index("test_doc", {"name": test_string})

        # search string
        response = self.searcher.search_string(test_string)
        self.assertEqual(response["total"], 1)

        self.searcher.index("not_test_doc", {"value": test_string})

        response = self.searcher.search_string(test_string)
        self.assertEqual(response["total"], 2)

    def test_field(self):
        test_string = "A test string"
        test_object = {
            "name": test_string,
            "tags": {
                "tag_one": "one",
                "tag_two": "two"
            },
            "fieldX": "valueY"
        }
        self.searcher.index("test_doc", test_object)

        # search tags
        response = self.searcher.search_fields({"tags.tag_one": "one"})
        self.assertEqual(response["total"], 1)

        # search tags
        response = self.searcher.search_fields({"tags.tag_one": "one", "tags.tag_two": "two"})
        self.assertEqual(response["total"], 1)

        response = self.searcher.search_fields({"fieldX": "valueY"})
        self.assertEqual(response["total"], 1)

        # search tags
        response = self.searcher.search_fields({"tags.tag_one": "one", "tags.tag_two": "not_two"})
        self.assertEqual(response["total"], 0)

    def test_search_string_and_field(self):
        test_object = {
            "name": "You may find me in a coffee shop",
            "course_id": "A/B/C",
            "abc": "xyz",
        }
        self.searcher.index("test_doc", test_object)

        response = self.searcher.search(query_string="find me")
        self.assertEqual(response["total"], 1)

        response = self.searcher.search_fields({"course_id": "A/B/C"})
        self.assertEqual(response["total"], 1)

        response = self.searcher.search(query_string="find me", field_dictionary={"course_id": "X/Y/Z"})
        self.assertEqual(response["total"], 0)

        response = self.searcher.search(query_string="find me", field_dictionary={"course_id": "A/B/C"})
        self.assertEqual(response["total"], 1)

        response = self.searcher.search_string("find me", field_dictionary={"course_id": "A/B/C"})
        self.assertEqual(response["total"], 1)

        response = self.searcher.search_fields({"course_id": "A/B/C"}, query_string="find me")
        self.assertEqual(response["total"], 1)

    def test_search_tags(self):
        test_object = {
            "name": "John Lester",
            "course_id": "A/B/C",
            "abc": "xyz"
        }
        tags = {
            "color": "red",
            "shape": "square",
            "taste": "sour",
        }
        self.searcher.index("test_doc", test_object, tags=tags)

        response = self.searcher.search_tags({"color": "red"})
        self.assertEqual(response["total"], 1)
        result = response["results"][0]
        self.assertEqual(result["tags"]["color"], "red")
        self.assertEqual(result["tags"]["shape"], "square")
        self.assertEqual(result["tags"]["taste"], "sour")

        response = self.searcher.search(tag_dictionary={"color": "red"})
        self.assertEqual(response["total"], 1)
        result = response["results"][0]
        self.assertEqual(result["tags"]["color"], "red")
        self.assertEqual(result["tags"]["shape"], "square")
        self.assertEqual(result["tags"]["taste"], "sour")

        response = self.searcher.search(tag_dictionary={"color": "blue"})
        self.assertEqual(response["total"], 0)

        response = self.searcher.search(tag_dictionary={"shape": "square"})
        self.assertEqual(response["total"], 1)
        result = response["results"][0]
        self.assertEqual(result["tags"]["color"], "red")
        self.assertEqual(result["tags"]["shape"], "square")
        self.assertEqual(result["tags"]["taste"], "sour")

        response = self.searcher.search(tag_dictionary={"shape": "round"})
        self.assertEqual(response["total"], 0)

        response = self.searcher.search(tag_dictionary={"shape": "square", "color": "red"})
        self.assertEqual(response["total"], 1)
        result = response["results"][0]
        self.assertEqual(result["tags"]["color"], "red")
        self.assertEqual(result["tags"]["shape"], "square")
        self.assertEqual(result["tags"]["taste"], "sour")

        response = self._searcher.search(tag_dictionary={"shape": "square", "color": "blue"})
        self.assertEqual(response["total"], 0)
