"""
This test will run for firebase_token_generator.py.
"""
import unittest

from xmodule.firebase_token_generator import _encode, _encode_json, _encode_token, create_token


class TokenGenerator(unittest.TestCase):
    """
    Tests for the file firebase_token_generator.py
    """
    def test_encode(self):
        """
        This tests makes sure that no matter what version of python
        you have, the _encode function still returns the appropriate result
        for a string.
        """
        expected = "dGVzdDE"
        result = _encode("test1")
        self.assertEqual(expected, result)

    def test_encode_json(self):
        """
        Same as above, but this one focuses on a python dict type
        transformed into a json object and then encoded.
        """
        expected = "eyJ0d28iOiAidGVzdDIiLCAib25lIjogInRlc3QxIn0"
        result = _encode_json({'one': 'test1', 'two': 'test2'})
        self.assertEqual(expected, result)

    def test_create_token(self):
        """
        Unlike its counterpart in student/views.py, this function
        just checks for the encoding of a token. The other function
        will test depending on time and user.
        """
        expected = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJ1c2VySWQiOiAidXNlcm5hbWUiLCAidHRsIjogODY0MDB9.-p1sr7uwCapidTQ0qB7DdU2dbF-hViKpPNN_5vD10t8"
        result1 = _encode_token('4c7f4d1c-8ac4-4e9f-84c8-b271c57fcac4', {"userId": "username", "ttl": 86400})
        result2 = create_token('4c7f4d1c-8ac4-4e9f-84c8-b271c57fcac4', {"userId": "username", "ttl": 86400})
        self.assertEqual(expected, result1)
        self.assertEqual(expected, result2)
