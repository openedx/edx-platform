"""
Tests for the ElasticDatabase class in es_requests
"""

import json
import time
import os

from django.test import TestCase
import requests
from pyfuzz.generator import random_regex
from django.test.utils import override_settings

from search.es_requests import ElasticDatabase, flaky_request
from mocks import StubServer, StubRequestHandler


class PersonalServer(StubServer):
    """
    SubServer implementation for ElasticSearch mocking
    """

    def log_request(self, request_type, path, content):
        self.requests.append(self.request(request_type, path, content))
        if request_type == "POST":
            if path.endswith("/test-index/test-type/"):
                self.status_code = 201
            elif path.endswith("_bulk"):
                self.status_code = 200
        if request_type == "HEAD":
            if path.endswith("/test-index/test-type"):
                self.status_code = 200
            else:
                self.status_code = 404


@override_settings(ES_DATABASE="http://127.0.0.1:9203")
class EsTest(TestCase):
    """
    Test suite for ElasticDatabase class
    """

    def setUp(self):
        self.stub = PersonalServer(StubRequestHandler, 9203)
        es_instance = "http://127.0.0.1:9203"
        # Making sure that there is actually a running es_instance before testing
        database_request = requests.get(es_instance)
        self.assertEqual(database_request.status_code, 200)
        requests.put(es_instance)
        self.elastic_search = ElasticDatabase("common/djangoapps/search/tests/test_settings.json")
        index_request = setup_index(self.elastic_search.url, "test-index", self.elastic_search.index_settings)
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

    def test_index_data(self):
        fake_data = {"data": "Test String"}
        fake_data.update({"hash": random_regex(regex="[a-zA-Z0-9]", length=50)})
        fake_data.update({"type_hash": random_regex(regex="[a-zA-Z0-9]", length=50)})
        response = self.elastic_search.index_data("test-index", fake_data, "test-type", "1234")
        self.assertEqual(response.status_code, 201)

    def tearDown(self):
        delete_index(self.elastic_search.url, "test-index")
        self.stub.stop()


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
    return requests.post(full_url, data=json.dumps(dictionary))


def setup_index(url, index, settings):
    """
    Creates a new elasticsearch index, returns the response it gets
    """

    full_url = "/".join([url, index]) + "/"
    return flaky_request("put", full_url, data=json.dumps(settings))


def delete_index(url, index):
    """
    Deletes the index specified, along with all contained types and data
    """

    full_url = "/".join([url, index])
    return flaky_request("delete", full_url)
