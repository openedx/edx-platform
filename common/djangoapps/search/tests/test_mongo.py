"""
Test suite for the MongoIndexer class in es_requests
"""

from search.es_requests import MongoIndexer
from django.test import TestCase
from pymongo import MongoClient
import random
import string
from pyfuzz.generator import random_item, random_ascii
import json
from StringIO import StringIO
import ho.pisa as pisa
import urllib
import base64


def dummy_document(key, values, data_type, **kwargs):
    """
    Returns a document matching the key to a dictionary mapping each value to a random string

    kwargs is passed directly to the random_ascii method of pyfuzz
    """

    dummy_data = {}
    dummy_data[key] = {value: random_item(data_type, **kwargs) for value in values}
    return dummy_data


class MongoTest(TestCase):
    """
    Test suite for the MongoIndexer class
    """

    def setUp(self):
        self.host = "localhost"
        self.port = 27017
        self.client = MongoClient(self.host, self.port)
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
        self.indexer = MongoIndexer(self.host, self.port, content_database="test-content", module_database="test-module")

    def test_find_asset_name(self):
        file_id = dummy_document("files_id", ["name", "test_field"], "ascii", length=20)
        file_id["files_id"].update({"category": "asset"})
        self.chunk_collection.insert(file_id)
        cursor = self.indexer.find_asset_with_name(file_id["files_id"]["name"])
        self.assertEquals(cursor["files_id"], file_id["files_id"])

    def test_find_module_for_course(self):
        id_ = dummy_document("_id", ["tag", "org", "course", "category", "name"], "ascii", length=20)
        self.module_collection.insert(id_)
        cursor = self.indexer.find_modules_for_course(id_["_id"]["course"])
        self.assertEquals(cursor.next()["_id"], id_["_id"])

    def test_find_module_transcript(self):
        video_module = dummy_document("definition", ["data"], "ascii", length=200)
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        video_module["definition"]["data"] += test_string
        test_transcript = {"text": random_ascii(length=50)}
        test_document = {"files_id": {"name": "dJvsFg10JY"}, "data": json.dumps(test_transcript)}
        self.chunk_collection.insert(test_document)
        transcript = self.indexer.find_transcript_for_video_module(video_module).encode("utf-8", "ignore")
        self.assertEquals(transcript.replace(" ", ""), test_transcript["text"].replace(" ", ""))

        test_bad_transcript = {"definition": {"data": 10}}
        self.assertEquals(self.indexer.find_transcript_for_video_module(test_bad_transcript), [""])

    def test_pdf_to_text(self):
        pseudo_file = StringIO()
        pdf = pisa.CreatePDF("This is a test", pseudo_file)
        test = {"data": pseudo_file.getvalue()}
        test.update({"files_id": {"name": "testPdf"}})
        value = self.indexer.pdf_to_text(test)
        self.assertEquals(value.strip(), "This is a test")

        bad_test = {"data": "fake", "files_id": {"name":"testCase"}}
        self.assertEquals(self.indexer.pdf_to_text(bad_test), "")

    def test_problem_text(self):
        test_text = "<p>This is a test</p><text>and so is <a href='test.com'></a>this</text>"
        document = {"definition":{"data": test_text}}
        check = self.indexer.searchable_text_from_problem_data(document)
        self.assertEquals(check, "This is a test and so is this")

        bad_document = {"definition": {"data": "@#@%^%#$afsdkjjl@#!$%"}}
        bad_check = self.indexer.searchable_text_from_problem_data(bad_document)
        self.assertEquals(bad_check, " ")

    def test_youku_video(self):
        document = {"definition": {"data": "player.youku.com"}}
        image = self.indexer.thumbnail_from_video_module(document)
        url = "https://lh6.ggpht.com/8_h5j6hiFXdSl5atSJDf8bJBy85b3IlzNWeRzOqRurfNVI_oiEG-dB3C0vHRclOG8A=w170"
        test_image = urllib.urlopen(url)
        self.assertEquals(image, base64.b64encode(test_image.read()))

    def test_bad_video(self):
        document = {"definition": {"data": "blank"}}
        image = self.indexer.thumbnail_from_video_module(document)
        url = "http://img.youtube.com/vi/Tt9g2se1LcM/4.jpg"
        test_image = urllib.urlopen(url)
        self.assertEquals(image, base64.b64encode(test_image.read()))

    def test_good_thumbnail(self):
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        document = {"definition": {"data": test_string}}
        image = self.indexer.thumbnail_from_video_module(document)
        test_image = urllib.urlopen("http://img.youtube.com/vi/dJvsFg10JY/0.jpg")
        self.assertEquals(base64.b64encode(test_image.read()), image)

    def test_pdf_thumbnail(self):
        bad_pseduo_file = StringIO()
        bad_pdf = random_item("bytes", length=200)
        bad_pseduo_file.write(bad_pdf)
        try:
            self.indexer.thumbnail_from_pdf({"data": bad_pseduo_file.getvalue()})
        except:
            success = False
        self.assertFalse(success)

    def test_html_thumbnail(self):
        success = True
        try:
            self.indexer.thumbnail_from_html("<p>Test</p>")
        except:
            success = False
        self.assertTrue(success)

    def test_get_searchable_text(self):
        problem_test_text = "<p>This is a test</p><text>and so is <a href='test.com'></a>this</text>"
        problem_document = {"definition": {"data": problem_test_text}}
        problem_test = self.indexer.get_searchable_text(problem_document, "problem")
        self.assertEquals(problem_test, "This is a test and so is this")

        video_module = dummy_document("definition", ["data"], "ascii", length=200)
        test_string = '<video youtube=\"0.75:-gKKUBQ2NWA,1.0:dJvsFg10JY,1.25:lm3IKbRE2VA,1.50:Pz0XiZ8wO9o\">'
        video_module["definition"]["data"] += test_string
        test_transcript = {"text": random_ascii(length=50)}
        test_document = {"files_id": {"name": "dJvsFg10JY"}, "data": json.dumps(test_transcript)}
        self.chunk_collection.insert(test_document)
        transcript = self.indexer.get_searchable_text(video_module, "transcript").encode("utf-8", "ignore")
        self.assertEquals(transcript.replace(" ", ""), test_transcript["text"].replace(" ", ""))

    def tearDown(self):
        self.test_content.drop_collection("fs.chunks")
        self.test_content.drop_collection("fs.files")
        self.client.drop_database("test-content")

        self.test_module.drop_collection("modulestore")
        self.client.drop_database("test-module")
