from ..es_requests import MongoIndexer
from django.test import TestCase
from pymongo import MongoClient
import random
import string


def random_files(file_ending, test_files=10, filename_sizes=20,
                 valid_chars=string.lowercase+string.uppercase+string.digits):
    new_string = lambda: "".join(random.choice(valid_chars) for i in range(filename_sizes))+file_ending
    return (new_string() for i in range(test_files))


class MongoTest(TestCase):

    def setUp(self, host="localhost", port=27017):
        self.host = host
        self.port = port
        self.client = MongoClient(host, port)
        # Create test databases
        dummy = {"dummy": True}
        self.test_content = self.client["test-content"]
        self.test_module = self.client["test-module"]
        # Create expected collections
        self.chunk_collection = self.test_content["fs.chunks"]
        self.chunk_collection.insert(dummy)
        self.file_collection = self.test_content["fs.files"]
        self.file_collection.insert(dummy)
        self.module_collection = self.test_module["modulestore"]
        self.module_collection.insert(dummy)
        self.indexer = MongoIndexer(host, port, content_database="test-content", module_database="test-module")

    def test_incorrect_collection(self):
        """Test to make sure that trying to create an indexer on a non-existent collection will error"""
        success = False
        try:
            MongoIndexer(self.host, self.port, chunk_collection="fake-collection")
        except ValueError:
            success = True
        self.assertTrue(success)

    def test_find_files(self):
        file_ending = ".test"
        filenames = set(random_files(file_ending))
        for filename in filenames:
            self.file_collection.insert({"filename": filename})
        found = set(element["filename"] for element in self.indexer.find_files_with_type(file_ending))
        self.assertTrue(found == filenames)

    def test_find_chunks(self):
        file_ending = ".test"
        filenames = set(random_files(file_ending))
        for filename in filenames:
            self.chunk_collection.insert({"files_id": {"name": filename}})
        found = set(element["files_id"]["name"] for element in self.indexer.find_chunks_with_type(file_ending))
        self.assertTrue(found == filenames)

    def test_find_modules(self):
        category = "category"
        content_strings = set(random_files(""))
        for content_string in content_strings:
            self.module_collection.insert({"_id": {"category": category, "content": content_string}})
        found = set(element["_id"]["content"] for element in self.indexer.find_modules_by_category(category))
        self.assertTrue(found == content_strings)

    def tearDown(self):
        self.test_content.drop_collection("fs.chunks")
        self.test_content.drop_collection("fs.files")
        self.client.drop_database("test-content")

        self.test_module.drop_collection("modulestore")
        self.client.drop_database("test-module")
