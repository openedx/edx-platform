"""
Tests for the ElasticDatabase class in es_requests
"""

from django.test import TestCase
import requests
from search.es_requests import ElasticDatabase, flaky_request
import json
import time
import os


class EsTest(TestCase):
    """
    Test suite for ElasticDatabase class
    """

    def setUp(self):
        es_instance = "http://localhost:9200"
        # Making sure that there is actually a running es_instance before testing
        database_request = requests.get(es_instance)
        self.assertEqual(database_request.status_code, 200)
        self.elastic_search = ElasticDatabase("common/djangoapps/search/tests/test_settings.json")
        index_request = setup_index(self.elastic_search.url, "test-index", self.elastic_search.index_settings)
        print index_request.content
        self.assertEqual(index_request.status_code, 200)
        type_request = setup_type(
            self.elastic_search.url,
            "test-index",
            "test-type",
            "common/djangoapps/search/tests/test_mapping.json"
        )
        time.sleep(0.1)  # Without sleep, tests will run without setUp finishing.
        self.assertEqual(type_request.status_code, 201)
        self.current_path = os.path.dirname(os.path.abspath(__file__))

    def test_type_existence(self):
        self.assertTrue(has_type(self.elastic_search.url, "test-index", "test-type"))
        self.assertFalse(has_type(self.elastic_search.url, "test-index", "fake-type"))
        self.assertFalse(has_type(self.elastic_search.url, "fake-index", "test-type"))
        self.assertFalse(has_type(self.elastic_search.url, "fake-index", "fake-type"))

    def test_bulk_index(self):
        test_string = ""
        test_string += json.dumps({"index": {"_index": "test-index", "_type": "test-type", "_id": "10"}})
        test_string += "\n"
        test_string += json.dumps({"searchable_text": "some_text", "test-float": "1.0"})
        test_string += "\n"
        success = self.elastic_search.bulk_index(test_string)
        self.assertEqual(success.status_code, 200)

    def tearDown(self):
        self.elastic_search.delete_index("test-index")

def has_index(url, index):
    """
    Checks to see if the Elastic Search instance contains the given index,
    """

    full_url = "/".join([url, index])
    response = flaky_request("head", full_url)
    if response:
        return response.status_code == 200
    else:
        return False

def has_type(url, index, type_):
    """
    Same as has_index method, but for a given type
    """

    full_url = "/".join([url, index, type_])
    response = flaky_request("head", full_url)
    if response:
        return response.status_code == 200
    else:
        return False


def setup_type(url, index, type_, json_mapping):
    """
    Instantiates a type within the Elastic Search instance

    json_mapping should be a dictionary starting at the properties level of a mapping.

    The type level will be added, so if you include it things will break. The purpose of this
    is to encourage loose coupling between types and mappings for better code
    """

    full_url = "/".join([url, index, type_]) + "/"
    with open(json_mapping) as source:
        dictionary = json.load(source)
    return flaky_request("post", full_url, data=json.dumps(dictionary))


def setup_index(url, index, settings):
    """
    Creates a new elasticsearch index, returns the response it gets
    """

    full_url = "/".join([url, index]) + "/"
    return flaky_request("put", full_url, data=json.dumps(settings))
