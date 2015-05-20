"""
Tests for the SignatureValidator class.
"""

from django.test import TestCase
from django.test.client import RequestFactory
from mock import patch

from lti_provider.models import LtiConsumer
from lti_provider.signature_validator import SignatureValidator


class SignatureValidatorTest(TestCase):
    """
    Tests for the custom SignatureValidator class that uses the oauthlib library
    to check message signatures. Note that these tests mock out the library
    itself, since we assume it to be correct.
    """

    def test_valid_client_key(self):
        """
        Verify that check_client_key succeeds with a valid key
        """
        key = 'valid_key'
        self.assertTrue(SignatureValidator().check_client_key(key))

    def test_long_client_key(self):
        """
        Verify that check_client_key fails with a key that is too long
        """
        key = '0123456789012345678901234567890123456789'
        self.assertFalse(SignatureValidator().check_client_key(key))

    def test_empty_client_key(self):
        """
        Verify that check_client_key fails with a key that is an empty string
        """
        key = ''
        self.assertFalse(SignatureValidator().check_client_key(key))

    def test_null_client_key(self):
        """
        Verify that check_client_key fails with a key that is None
        """
        key = None
        self.assertFalse(SignatureValidator().check_client_key(key))

    def test_valid_nonce(self):
        """
        Verify that check_nonce succeeds with a key of maximum length
        """
        nonce = '0123456789012345678901234567890123456789012345678901234567890123'
        self.assertTrue(SignatureValidator().check_nonce(nonce))

    def test_long_nonce(self):
        """
        Verify that check_nonce fails with a key that is too long
        """
        nonce = '01234567890123456789012345678901234567890123456789012345678901234'
        self.assertFalse(SignatureValidator().check_nonce(nonce))

    def test_empty_nonce(self):
        """
        Verify that check_nonce fails with a key that is an empty string
        """
        nonce = ''
        self.assertFalse(SignatureValidator().check_nonce(nonce))

    def test_null_nonce(self):
        """
        Verify that check_nonce fails with a key that is None
        """
        nonce = None
        self.assertFalse(SignatureValidator().check_nonce(nonce))

    def test_validate_existing_key(self):
        """
        Verify that validate_client_key succeeds if the client key exists in the
        database
        """
        LtiConsumer.objects.create(consumer_key='client_key', consumer_secret='client_secret')
        self.assertTrue(SignatureValidator().validate_client_key('client_key', None))

    def test_validate_missing_key(self):
        """
        Verify that validate_client_key fails if the client key is not in the
        database
        """
        self.assertFalse(SignatureValidator().validate_client_key('client_key', None))

    def test_get_existing_client_secret(self):
        """
        Verify that get_client_secret returns the right value if the key is in
        the database
        """
        LtiConsumer.objects.create(consumer_key='client_key', consumer_secret='client_secret')
        secret = SignatureValidator().get_client_secret('client_key', None)
        self.assertEqual(secret, 'client_secret')

    def test_get_missing_client_secret(self):
        """
        Verify that get_client_secret returns None if the key is not in the
        database
        """
        secret = SignatureValidator().get_client_secret('client_key', None)
        self.assertIsNone(secret)

    @patch('oauthlib.oauth1.SignatureOnlyEndpoint.validate_request',
           return_value=(True, None))
    def test_verification_parameters(self, verify_mock):
        """
        Verify that the signature validaton library method is called using the
        correct parameters derived from the HttpRequest.
        """
        body = 'oauth_signature_method=HMAC-SHA1&oauth_version=1.0'
        content_type = 'application/x-www-form-urlencoded'
        request = RequestFactory().post('/url', body, content_type=content_type)
        headers = {'Content-Type': content_type}
        SignatureValidator().verify(request)
        verify_mock.assert_called_once_with(
            request.build_absolute_uri(), 'POST', body, headers)
