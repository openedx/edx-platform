"""
Tests for the CyberSource processor handler
"""
from collections import OrderedDict
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from shoppingcart.processors.CyberSource import *
from shoppingcart.processors.exceptions import CCProcessorSignatureException

TEST_CC_PROCESSOR = {
    'CyberSource' : {
        'SHARED_SECRET': 'secret',
        'MERCHANT_ID' : 'edx_test',
        'SERIAL_NUMBER' : '12345',
        'ORDERPAGE_VERSION': '7',
        'PURCHASE_ENDPOINT': '',
    }
}

@override_settings(CC_PROCESSOR=TEST_CC_PROCESSOR)
class CyberSourceTests(TestCase):

    def setUp(self):
        pass

    def test_override_settings(self):
        self.assertEquals(settings.CC_PROCESSOR['CyberSource']['MERCHANT_ID'], 'edx_test')
        self.assertEquals(settings.CC_PROCESSOR['CyberSource']['SHARED_SECRET'], 'secret')

    def test_hash(self):
        """
        Tests the hash function.  Basically just hardcodes the answer.
        """
        self.assertEqual(hash('test'), 'GqNJWF7X7L07nEhqMAZ+OVyks1Y=')
        self.assertEqual(hash('edx '), '/KowheysqM2PFYuxVKg0P8Flfk4=')

    def test_sign_then_verify(self):
        """
        "loopback" test:
        Tests the that the verify function verifies parameters signed by the sign function
        """
        params = OrderedDict()
        params['amount'] = "12.34"
        params['currency'] = 'usd'
        params['orderPage_transactionType'] = 'sale'
        params['orderNumber'] = "567"

        verify_signatures(sign(params), signed_fields_key='orderPage_signedFields',
                          full_sig_key='orderPage_signaturePublic')

        # if the above verify_signature fails it will throw an exception, so basically we're just
        # testing for the absence of that exception.  the trivial assert below does that
        self.assertEqual(1, 1)

    def test_verify_exception(self):
        """
        Tests that failure to verify raises the proper CCProcessorSignatureException
        """
        params = OrderedDict()
        params['a'] = 'A'
        params['b'] = 'B'
        params['signedFields'] = 'A,B'
        params['signedDataPublicSignature'] = 'WONTVERIFY'

        with self.assertRaises(CCProcessorSignatureException):
            verify_signatures(params)


