"""
This test will run for annotator_token.py
"""
import unittest

from xmodule.annotator_token import retrieve_token


class TokenRetriever(unittest.TestCase):
    """
    Tests to make sure that when passed in a username and secret token, that it will be encoded correctly
    """
    shard = 1

    def test_token(self):
        """
        Test for the token generator. Give an a random username and secret token,
        it should create the properly encoded string of text.
        """
        expected = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpYXQiOjE1NDg4NTUxNzYsImQiOnsiaXNzdWVkQXQiOiIyMDE5LTAxLTMwVDA4OjMyOjU2LjE1ODYzMS01OjAwIiwiY29uc3VtZXJLZXkiOiJmYWtlX3NlY3JldCIsInVzZXJJZCI6InVzZXJuYW1lIiwidWlkIjoidXNlcm5hbWUiLCJ0dGwiOjg2NDAwfSwidiI6MH0.tuzOcvKEEOW6V7FLlSr_CS_LbYBX_dvdxOWzXquivIU"
        response = retrieve_token("useremail", "userid", "fake_secret")

        # because the middle hashes are dependent on time, only the header and footer are checked for secret key
        self.assertEqual(expected.split('.')[0], response.split('.')[0])
        self.assertNotEqual(expected.split('.')[2], response.split('.')[2])
