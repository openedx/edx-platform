"""
Test suite for the MongoIndexer class in es_requests
"""

from StringIO import StringIO
import json

from django.test import TestCase
from django.test.utils import override_settings

from pymongo import MongoClient
from pyfuzz.generator import random_item

from search.es_requests import MongoIndexer, MalformedDataException


def dummy_document(key, values, data_type, **kwargs):
    """
    Returns a document matching the key to a dictionary mapping each value to a random string

    kwargs is passed directly to the random_item method of pyfuzz
    """

    dummy_data = {}
    dummy_data[key] = {value: random_item(data_type, **kwargs) for value in values}
    return dummy_data


class MongoTest(TestCase):
    """
    Test suite for the MongoIndexer class
    """

    @override_settings(CONTENTSTORE={'OPTIONS': {'db': 'test-content'}})
    @override_settings(MODULESTORE={'default': {'OPTIONS': {'db': 'test-module', 'host': 'localhost'}}})
    def setUp(self):
        self.client = MongoClient('localhost', 27017)
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
        self.indexer = MongoIndexer()

    def test_find_module_for_course(self):
        id_ = dummy_document("_id", ["tag", "org", "course", "category", "name"], "ascii", length=20)
        self.module_collection.insert(id_)
        cursor = self.indexer._find_modules_for_course(id_["_id"]["course"])
        self.assertEquals(cursor.next()["_id"], id_["_id"])

    def test_find_module_transcript(self):
        video_module = dummy_document("definition", ["data"], "ascii", length=200)
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        video_module["definition"]["data"] += test_string
        test_transcript = {"text": random_item("ascii", length=50)}
        test_document = {"files_id": {"name": "dJvsFg10JY"}, "data": json.dumps(test_transcript)}
        self.chunk_collection.insert(test_document)
        transcript = self.indexer._find_transcript_for_video_module(video_module).encode("utf-8", "ignore")
        self.assertEquals(transcript.replace(" ", ""), test_transcript["text"].replace(" ", ""))

        test_bad_transcript = {"definition": {"data": 10}}
        success = False
        try:
            self.indexer._find_transcript_for_video_module(test_bad_transcript), [""]
        except MalformedDataException:
            success = True
        self.assertTrue(success)

    def test_problem_text(self):
        test_text = "<p>This is a test</p><text>and so is <a href='test.com'></a>this</text>"
        document = {"definition": {"data": test_text}}
        check = self.indexer._get_searchable_text_from_problem_data(document)
        self.assertEquals(check, "This is a test and so is this")

        bad_document = {"definition": {"data": "@#@%^%#$afsdkjjl@#!$%"}}
        success = False
        try:
            bad_check = self.indexer._get_searchable_text_from_problem_data(bad_document)
        except MalformedDataException:
            success = True
        self.assertTrue(success)

    def test_youku_video(self):
        document = {"definition": {"data": "player.youku.com"}}
        image = self.indexer._get_thumbnail_from_video_module(document)
        url = "https://lh6.ggpht.com/8_h5j6hiFXdSl5atSJDf8bJBy85b3IlzNWeRzOqRurfNVI_oiEG-dB3C0vHRclOG8A=w170"
        self.assertEquals(image, url)

    def test_bad_video(self):
        document = {"definition": {"data": "<video asdfghjkl>"}}
        success = False
        try:
            image = self.indexer._get_thumbnail_from_video_module(document)
        except MalformedDataException:
            success = True
        self.assertTrue(success)

    def test_good_thumbnail(self):
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        document = {"definition": {"data": test_string}}
        image = self.indexer._get_thumbnail_from_video_module(document)
        url = "http://img.youtube.com/vi/dJvsFg10JY/0.jpg"
        self.assertEquals(url, image)

    def test_pdf_thumbnail(self):
        bad_pseduo_file = StringIO()
        bad_pdf = random_item("bytes", length=200)
        bad_pseduo_file.write(bad_pdf)
        try:
            self.indexer._get_thumbnail_from_pdf({"data": bad_pseduo_file.getvalue()})
        except:
            success = False
        self.assertFalse(success)

    def test_html_thumbnail(self):
        success = True
        try:
            self.indexer._get_thumbnail_from_html("<p>Test</p>")
        except:
            success = False
        self.assertTrue(success)

    def test_get_searchable_text(self):
        problem_test_text = "<p>This is a test</p><text>and so is <a href='test.com'></a>this</text>"
        problem_document = {"definition": {"data": problem_test_text}}
        problem_test = self.indexer._get_searchable_text(problem_document, "problem")
        self.assertEquals(problem_test, "This is a test and so is this")

        video_module = dummy_document("definition", ["data"], "ascii", length=200)
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        video_module["definition"]["data"] += test_string
        test_transcript = {"text": random_item("ascii", length=50)}
        test_document = {"files_id": {"name": "dJvsFg10JY"}, "data": json.dumps(test_transcript)}
        self.chunk_collection.insert(test_document)
        transcript = self.indexer._get_searchable_text(video_module, "transcript").encode("utf-8", "ignore")
        self.assertEquals(transcript.replace(" ", ""), test_transcript["text"].replace(" ", ""))

    def test_bulk_index_item(self):
        data = {"type_hash": "test type hash", "hash": "test hash"}
        bulk_index = self.indexer._get_bulk_index_item("test-index", data)
        action = json.loads(bulk_index.split("\n")[0])
        self.assertEquals(action["index"]["_index"], "test-index")
        self.assertEquals(action["index"]["_type"], "test type hash")

    def test_index_course_problem(self):
        document = dummy_document("_id", ["org", "name"], "regex", regex="[a-zA-Z0-9]", length=50)
        document["_id"].update({"category": "problem", "course": "test-course"})
        asset_string = "<p>Test</p>"
        document.update({"definition": {"data": asset_string}})
        self.module_collection.insert(document)
        course_document = {"_id": {"category": "course", "course": document["_id"]["course"], "name": "test_course"}}
        self.module_collection.insert(course_document)
        self.indexer.index_course("test-course")

    def test_index_course_pdf(self):
        document = dummy_document("_id", ["org"], "regex", regex="[a-zA-Z0-9]", length=50)
        document["_id"].update({"category": "html", "course": "test-course"})
        random_asset_name = random_item("regex", regex="[a-zA-Z0-9]", length=50)
        asset_string = "/asset/%s.pdf" % random_asset_name
        document.update({"definition": {"data": asset_string}})
        self.module_collection.insert(document)

        course_document = {"_id": {"category": "course", "course": document["_id"]["course"], "name": "test_course"}}
        self.module_collection.insert(course_document)
        check = self.indexer.index_course("test-course")
        self.assertEquals(check, None)

    def tearDown(self):
        self.test_content.drop_collection("fs.chunks")
        self.test_content.drop_collection("fs.files")
        self.client.drop_database("test-content")

        self.test_module.drop_collection("modulestore")
        self.client.drop_database("test-module")
