"""
Tests for the SignatureValidator class.
"""


import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from mock import patch

from lms.djangoapps.lti_provider.models import LtiConsumer
from lms.djangoapps.lti_provider.signature_validator import SignatureValidator


def get_lti_consumer():
    """
    Helper method for all Signature Validator tests to get an LtiConsumer object.
    """
    return LtiConsumer(
        consumer_name='Consumer Name',
        consumer_key='Consumer Key',
        consumer_secret='Consumer Secret'
    )


@ddt.ddt
class ClientKeyValidatorTest(TestCase):
    """
    Tests for the check_client_key method in the SignatureValidator class.
    """

    def setUp(self):
        super(ClientKeyValidatorTest, self).setUp()
        self.lti_consumer = get_lti_consumer()

    def test_valid_client_key(self):
        """
        Verify that check_client_key succeeds with a valid key
        """
        key = self.lti_consumer.consumer_key
        self.assertTrue(SignatureValidator(self.lti_consumer).check_client_key(key))

    @ddt.data(
        ('0123456789012345678901234567890123456789',),
        ('',),
        (None,),
    )
    @ddt.unpack
    def test_invalid_client_key(self, key):
        """
        Verify that check_client_key fails with a disallowed key
        """
        self.assertFalse(SignatureValidator(self.lti_consumer).check_client_key(key))


@ddt.ddt
class NonceValidatorTest(TestCase):
    """
    Tests for the check_nonce method in the SignatureValidator class.
    """

    def setUp(self):
        super(NonceValidatorTest, self).setUp()
        self.lti_consumer = get_lti_consumer()

    def test_valid_nonce(self):
        """
        Verify that check_nonce succeeds with a key of maximum length
        """
        nonce = '0123456789012345678901234567890123456789012345678901234567890123'
        self.assertTrue(SignatureValidator(self.lti_consumer).check_nonce(nonce))

    @ddt.data(
        ('01234567890123456789012345678901234567890123456789012345678901234',),
        ('',),
        (None,),
    )
    @ddt.unpack
    def test_invalid_nonce(self, nonce):
        """
        Verify that check_nonce fails with badly formatted nonce
        """
        self.assertFalse(SignatureValidator(self.lti_consumer).check_nonce(nonce))


class SignatureValidatorTest(TestCase):
    """
    Tests for the custom SignatureValidator class that uses the oauthlib library
    to check message signatures. Note that these tests mock out the library
    itself, since we assume it to be correct.
    """

    def setUp(self):
        super(SignatureValidatorTest, self).setUp()
        self.lti_consumer = get_lti_consumer()

    def test_get_existing_client_secret(self):
        """
        Verify that get_client_secret returns the right value for the correct
        key
        """
        key = self.lti_consumer.consumer_key
        secret = SignatureValidator(self.lti_consumer).get_client_secret(key, None)
        self.assertEqual(secret, self.lti_consumer.consumer_secret)

    @patch('oauthlib.oauth1.SignatureOnlyEndpoint.validate_request',
           return_value=(True, None))
    def test_verification_parameters(self, verify_mock):
        """
        Verify that the signature validaton library method is called using the
        correct parameters derived from the HttpRequest.
        """
        body = u'oauth_signature_method=HMAC-SHA1&oauth_version=1.0'
        content_type = 'application/x-www-form-urlencoded'
        request = RequestFactory().post('/url', body, content_type=content_type)
        headers = {'Content-Type': content_type}
        SignatureValidator(self.lti_consumer).verify(request)
        verify_mock.assert_called_once_with(
            request.build_absolute_uri(), 'POST', body.encode('utf-8'), headers)
