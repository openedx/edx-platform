from django.test import TestCase
import requests
from ..es_requests import ElasticDatabase, PyGrep
import json
import time
import os


class EsTest(TestCase):

    def setUp(self, es_instance="http://localhost:9200"):
        # Making sure that there is actually a running es_instance before testing
        database_request = requests.get(es_instance)
        self.assertEqual(database_request.status_code, 200)
        self.elastic_search = ElasticDatabase(es_instance, "common/djangoapps/search/tests/test_settings.json")
        type_request = self.elastic_search.setup_type("test-index", "test-type",
                                                      "common/djangoapps/search/tests/test_mapping.json")
        time.sleep(0.1)  # Without sleep, tests will run without setUp finishing.
        self.assertEqual(type_request.status_code, 201)
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.crawler = PyGrep(self.current_path)

    def test_index_creation(self):
        settings = self.elastic_search.get_index_settings("test-index")["test-index"]["settings"]
        self.assertTrue(self.elastic_search.has_index("test-index"))
        self.assertFalse(self.elastic_search.has_index("fake-index"))
        self.assertEqual(settings["index.number_of_replicas"], "1")
        self.assertEqual(settings["index.number_of_shards"], "5")

    def test_type_existence(self):
        self.assertTrue(self.elastic_search.has_type("test-index", "test-type"))
        self.assertFalse(self.elastic_search.has_type("test-index", "fake-type"))
        self.assertFalse(self.elastic_search.has_type("fake-index", "test-type"))
        self.assertFalse(self.elastic_search.has_type("fake-index", "fake-type"))

    def test_type_creation(self):
        type_mapping = self.elastic_search.get_type_mapping("test-index", "test-type")
        self.assertTrue("properties" in type_mapping["test-type"].keys())
        self.assertTrue("test-float" in type_mapping["test-type"]["properties"]["mappings"]["properties"].keys())
        self.assertTrue("test-string" in type_mapping["test-type"]["properties"]["mappings"]["properties"].keys())

    def test_directory_search(self):
        relative_paths = ["/testdir/malformed.srt.sjson", "/testdir/transcript.srt.sjson",
                          "/testdir/nested/goal.srt.sjson"]
        absolute_paths = set([self.current_path+item for item in relative_paths])
        paths = self.crawler.grab_all_files_with_ending(".srt.sjson")
        flat_paths = set([item for sublist in paths for item in sublist])
        self.assertTrue(flat_paths == absolute_paths)

    def test_alternate_directory_search(self):
        relative_paths = ["/testdir/extension.foo", "/testdir/nested/extension2.foo"]
        absolute_paths = set([self.current_path+item for item in relative_paths])
        paths = self.crawler.grab_all_files_with_ending(".foo")
        flat_paths = set([item for sublist in paths for item in sublist])
        self.assertTrue(flat_paths == absolute_paths)
        success = False
        try:
            self.crawler.grab_all_files_with_ending(".fake").next()
        except StopIteration:
            success = True
        except:
            success = False
        self.assertTrue(success)

    def test_data_indexing(self):
        responses = self.elastic_search.index_directory_files(self.current_path, "test-index", "test-type",
                                                              silent=True, file_ending=".srt.sjson",
                                                              callback=self.elastic_search.index_transcript)
        successes = [json.loads(response)["ok"] for response in responses]
        correct_indices = [json.loads(response)["_index"] == "test-index" for response in responses]
        correct_types = [json.loads(response)["_type"] == "test-type" for response in responses]
        self.assertTrue(all(successes))
        self.assertTrue(all(correct_indices))
        self.assertTrue(all(correct_types))

    def test_data_failure(self):
        success = False
        path = self.current_path + "/testdir/malformed.srt.sjson"
        try:
            self.elastic_search.index_transcript("test-index", "test-type", path)
        except ValueError:
            success = True
        except:
            success = False
        self.assertTrue(success)

    def test_data_read(self):
        relative_paths = ["/testdir/malformed.srt.sjson", "/testdir/transcript.srt.sjson"]
        bad_response = self.elastic_search.index_transcript("test-index", "test-type",
                                                            self.current_path+relative_paths[0],
                                                            silent=True, id_="1")
        good_response = self.elastic_search.index_transcript("test-index", "test-type",
                                                             self.current_path+relative_paths[1],
                                                             silent=False, id_="2")
        self.assertEqual(bad_response.status_code, 201)
        self.assertEqual(good_response.status_code, 201)
        bad_object = self.elastic_search.get_data("test-index", "test-type", "1")
        good_object = self.elastic_search.get_data("test-index", "test-type", "2")
        self.assertEqual(bad_object.status_code, 200)
        self.assertEqual(good_object.status_code, 200)
        self.assertEqual(json.loads(bad_object._content)["_source"]["searchable_text"], "INVALID JSON")
        self.assertEqual(json.loads(good_object._content)["_source"]["searchable_text"], "Success!")

    def tearDown(self):
        self.elastic_search.delete_type("test-index", "test-type")
        self.elastic_search.delete_index("test-index")
