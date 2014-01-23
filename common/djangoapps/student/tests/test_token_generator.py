"""
This test will run for firebase_token_generator.py.
"""
import unittest
from datetime import datetime, timedelta

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.test.client import RequestFactory
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from django.http import HttpResponse

from mock import Mock, patch, sentinel

from student.firebase_token_generator import _encode, _encode_json, _encode_token, create_token

import shoppingcart
class TokenGenerator(TestCase):
    """
    Tests for the Token Generator
    """
    def test_encode(self):
        expected = "dGVzdDE"
        result = _encode("test1")
        self.assertEqual(expected, result)

    def test_encode_json(self):
        expected = "eyJ0d28iOiAidGVzdDIiLCAib25lIjogInRlc3QxIn0"
        result = _encode_json({'one': 'test1', 'two': 'test2'})
        self.assertEqual(expected, result)

    def test_create_token(self):
        expected = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VySWQiOiAidXNlcm5hbWUiLCAidHRsIjogODY0MDB9.-p1sr7uwCapidTQ0qB7DdU2dbF-hViKpPNN_5vD10t8"
        result1 = _encode_token('4c7f4d1c-8ac4-4e9f-84c8-b271c57fcac4', {"userId": "username", "ttl": 86400})
        result2 = create_token('4c7f4d1c-8ac4-4e9f-84c8-b271c57fcac4', {"userId": "username", "ttl": 86400})
        self.assertEqual(expected, result1)
        self.assertEqual(expected, result2)
