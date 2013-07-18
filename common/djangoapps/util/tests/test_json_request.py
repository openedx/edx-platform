from django.http import HttpResponse
from util.json_request import JsonResponse
import json
import unittest
import mock


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

    def test_set_status_kwarg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponse(obj, status=404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json")

    def test_set_status_arg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponse(obj, 404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json")

    def test_encoder(self):
        obj = [1, 2, 3]
        encoder = object()
        with mock.patch.object(json, "dumps", return_value="[1,2,3]") as dumps:
            resp = JsonResponse(obj, encoder=encoder)
        self.assertEqual(resp.status_code, 200)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        kwargs = dumps.call_args[1]
        self.assertIs(kwargs["cls"], encoder)
