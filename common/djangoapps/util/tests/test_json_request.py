from django.http import HttpResponse
from util.json_request import JsonResponse
import json
import unittest


class JsonResponseTestCase(unittest.TestCase):
    def test_empty(self):
        resp = JsonResponse()
        self.assertIsInstance(resp, HttpResponse)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["content-type"], "application/json")

    def test_empty_string(self):
        resp = JsonResponse("")
        self.assertIsInstance(resp, HttpResponse)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["content-type"], "application/json")

    def test_string(self):
        resp = JsonResponse("foo")
        self.assertEqual(resp.content, '"foo"')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/json")

    def test_dict(self):
        obj = {"foo": "bar"}
        resp = JsonResponse(obj)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/json")

    def test_set_status(self):
        obj = {"error": "resource not found"}
        resp = JsonResponse(obj, status=404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json")
