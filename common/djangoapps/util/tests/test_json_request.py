"""
Test for JsonResponse and JsonResponseBadRequest util classes.
"""

from django.http import HttpResponse, HttpResponseBadRequest
from util.json_request import JsonResponse, JsonResponseBadRequest
import json
import unittest
import mock


class JsonResponseTestCase(unittest.TestCase):
    """
    A set of tests to make sure that JsonResponse Class works correctly.
    """
    def test_empty(self):
        resp = JsonResponse()
        self.assertIsInstance(resp, HttpResponse)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_empty_string(self):
        resp = JsonResponse("")
        self.assertIsInstance(resp, HttpResponse)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_string(self):
        resp = JsonResponse("foo")
        self.assertEqual(resp.content, '"foo"')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_dict(self):
        obj = {"foo": "bar"}
        resp = JsonResponse(obj)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_set_status_kwarg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponse(obj, status=404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_set_status_arg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponse(obj, 404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

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


class JsonResponseBadRequestTestCase(unittest.TestCase):
    """
    A set of tests to make sure that the JsonResponseBadRequest wrapper class
    works as intended.
    """

    def test_empty(self):
        resp = JsonResponseBadRequest()
        self.assertIsInstance(resp, HttpResponseBadRequest)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_empty_string(self):
        resp = JsonResponseBadRequest("")
        self.assertIsInstance(resp, HttpResponse)
        self.assertEqual(resp.content, "")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_dict(self):
        obj = {"foo": "bar"}
        resp = JsonResponseBadRequest(obj)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_set_status_kwarg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponseBadRequest(obj, status=404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_set_status_arg(self):
        obj = {"error": "resource not found"}
        resp = JsonResponseBadRequest(obj, 404)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp["content-type"], "application/json; charset=utf-8")

    def test_encoder(self):
        obj = [1, 2, 3]
        encoder = object()
        with mock.patch.object(json, "dumps", return_value="[1,2,3]") as dumps:
            resp = JsonResponseBadRequest(obj, encoder=encoder)
        self.assertEqual(resp.status_code, 400)
        compare = json.loads(resp.content)
        self.assertEqual(obj, compare)
        kwargs = dumps.call_args[1]
        self.assertIs(kwargs["cls"], encoder)
