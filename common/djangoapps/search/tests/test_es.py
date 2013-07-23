from django.test import TestCase
import requests
from ..es_requests import ElasticDatabase


class EsTest(TestCase):

    def setUp(self, es_instance="http://localhost:9200"):
        # Making sure that there is actually a running es_instance before testing
        database_request = requests.get(es_instance)
        print database_request._content
        self.assertEqual(database_request.status_code, 200)
        self.elastic_search = ElasticDatabase(es_instance, "common/djangoapps/search/tests/test_settings.json")
        self.assertEqual(isinstance(self.elastic_search, ElasticDatabase), True)
        index_request = self.elastic_search.setup_index("test-index")
        print index_request._content
        self.assertEqual(index_request.status_code, 200)
        type_request = self.elastic_search.setup_type("test-index", "test_type",
                                                      "common/djangoapps/search/tests/test_mapping.json")
        print type_request._content
        self.assertEqual(type_request.status_code, 200)

    def test_index_creation(self):
        settings = self.elastic_search.get_index_settings("test-index")["test-index"]["settings"]
        self.assertEqual(self.elastic_search.has_index("test-index"), True)
        self.assertEqual(settings["index.number_of_replicas"], "5")
        self.assertEqual(settings["index.number_of_shards"], "10")

    def test_type_creation(self):
        check = self.elastic_search.get_type_mapping("test-index", "test-type")
        print check
        self.assertEqual(True, False)

    def tearDown(self):
        self.elastic_search.delete_type("test-index", "test-type")
        self.elastic_search.delete_index("test-index")
