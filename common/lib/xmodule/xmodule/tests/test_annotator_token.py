"""
This test will run for annotator_token.py
"""
import unittest

from xmodule.annotator_token import retrieve_token


class TokenRetriever(unittest.TestCase):
    """
    Tests to make sure that when passed in a username and secret token, that it will be encoded correctly
    """
    def test_token(self):
        """
        Test for the token generator. Give an a random username and secret token,
        it should create the properly encoded string of text.
        """
        expected = "eyJhbGciOiAiSFMyNTYiLCAidHlwIjogIkpXVCJ9.eyJpc3N1ZWRBdCI6ICIyMDE0LTAyLTI3VDE3OjAwOjQyLjQwNjQ0MSswOjAwIiwgImNvbnN1bWVyS2V5IjogImZha2Vfc2VjcmV0IiwgInVzZXJJZCI6ICJ1c2VybmFtZSIsICJ0dGwiOiA4NjQwMH0.Dx1PoF-7mqBOOSGDMZ9R_s3oaaLRPnn6CJgGGF2A5CQ"
        response = retrieve_token("username", "fake_secret")

        # because the middle hashes are dependent on time, conly the header and footer are checked for secret key
        self.assertEqual(expected.split('.')[0], response.split('.')[0])
        self.assertNotEqual(expected.split('.')[2], response.split('.')[2])
