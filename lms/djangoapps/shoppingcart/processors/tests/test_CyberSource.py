"""
Tests for the CyberSource processor handler
"""
from collections import OrderedDict
from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from student.tests.factories import UserFactory
from shoppingcart.models import Order, OrderItem
from shoppingcart.processors.helpers import get_processor_config
from shoppingcart.processors.exceptions import (
    CCProcessorException,
    CCProcessorSignatureException,
    CCProcessorDataException,
    CCProcessorWrongAmountException
)
from shoppingcart.processors.CyberSource import (
    render_purchase_form_html,
    process_postpay_callback,
    processor_hash,
    verify_signatures,
    sign,
    REASONCODE_MAP,
    record_purchase,
    get_processor_decline_html,
    get_processor_exception_html,
    payment_accepted,
)
from mock import patch, Mock


TEST_CC_PROCESSOR_NAME = "CyberSource"
TEST_CC_PROCESSOR = {
    'CyberSource': {
        'SHARED_SECRET': 'secret',
        'MERCHANT_ID': 'edx_test',
        'SERIAL_NUMBER': '12345',
        'ORDERPAGE_VERSION': '7',
        'PURCHASE_ENDPOINT': '',
        'microsites': {
            'test_microsite': {
                'SHARED_SECRET': 'secret_override',
                'MERCHANT_ID': 'edx_test_override',
                'SERIAL_NUMBER': '12345_override',
                'ORDERPAGE_VERSION': '7',
                'PURCHASE_ENDPOINT': '',
            }
        }
    }
}


def fakemicrosite(name, default=None):
    """
    This is a test mocking function to return a microsite configuration
    """
    if name == 'cybersource_config_key':
        return 'test_microsite'
    else:
        return None


@override_settings(
    CC_PROCESSOR_NAME=TEST_CC_PROCESSOR_NAME,
    CC_PROCESSOR=TEST_CC_PROCESSOR
)
class CyberSourceTests(TestCase):

    def test_override_settings(self):
        self.assertEqual(settings.CC_PROCESSOR['CyberSource']['MERCHANT_ID'], 'edx_test')
        self.assertEqual(settings.CC_PROCESSOR['CyberSource']['SHARED_SECRET'], 'secret')

    def test_microsite_no_override_settings(self):
        self.assertEqual(get_processor_config()['MERCHANT_ID'], 'edx_test')
        self.assertEqual(get_processor_config()['SHARED_SECRET'], 'secret')

    @patch("microsite_configuration.microsite.get_value", fakemicrosite)
    def test_microsite_override_settings(self):
        self.assertEqual(get_processor_config()['MERCHANT_ID'], 'edx_test_override')
        self.assertEqual(get_processor_config()['SHARED_SECRET'], 'secret_override')

    def test_hash(self):
        """
        Tests the hash function.  Basically just hardcodes the answer.
        """
        self.assertEqual(processor_hash('test'), 'GqNJWF7X7L07nEhqMAZ+OVyks1Y=')
        self.assertEqual(processor_hash('edx '), '/KowheysqM2PFYuxVKg0P8Flfk4=')

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

    def test_sign_then_verify_unicode(self):
        """
        Similar to the test above, which loops back to the original.
        Testing to make sure we can handle unicode parameters
        """
        params = {
            'card_accountNumber': '1234',
            'card_cardType': '001',
            'billTo_firstName': u'\u2699',
            'billTo_lastName': u"\u2603",
            'orderNumber': '1',
            'orderCurrency': 'usd',
            'decision': 'ACCEPT',
            'ccAuthReply_amount': '0.00'
        }

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

    def test_get_processor_decline_html(self):
        """
        Tests the processor decline html message
        """
        DECISION = 'REJECT'
        for code, reason in REASONCODE_MAP.iteritems():
            params = {
                'decision': DECISION,
                'reasonCode': code,
            }
            html = get_processor_decline_html(params)
            self.assertIn(DECISION, html)
            self.assertIn(reason, html)
            self.assertIn(code, html)
            self.assertIn(settings.PAYMENT_SUPPORT_EMAIL, html)

    def test_get_processor_exception_html(self):
        """
        Tests the processor exception html message
        """
        for type in [CCProcessorSignatureException, CCProcessorWrongAmountException, CCProcessorDataException]:
            error_msg = "An exception message of with exception type {0}".format(str(type))
            exception = type(error_msg)
            html = get_processor_exception_html(exception)
            self.assertIn(settings.PAYMENT_SUPPORT_EMAIL, html)
            self.assertIn('Sorry!', html)
            self.assertIn(error_msg, html)

        # test base case
        self.assertIn("EXCEPTION!", get_processor_exception_html(CCProcessorException()))

    def test_record_purchase(self):
        """
        Tests record_purchase with good and without returned CCNum
        """
        student1 = UserFactory()
        student1.save()
        student2 = UserFactory()
        student2.save()
        params_cc = {'card_accountNumber': '1234', 'card_cardType': '001', 'billTo_firstName': student1.first_name}
        params_nocc = {'card_accountNumber': '', 'card_cardType': '002', 'billTo_firstName': student2.first_name}
        order1 = Order.get_cart_for_user(student1)
        order2 = Order.get_cart_for_user(student2)
        record_purchase(params_cc, order1)
        record_purchase(params_nocc, order2)
        self.assertEqual(order1.bill_to_first, student1.first_name)
        self.assertEqual(order1.status, 'purchased')

        order2 = Order.objects.get(user=student2)
        self.assertEqual(order2.bill_to_first, student2.first_name)
        self.assertEqual(order2.status, 'purchased')

    def test_payment_accepted_invalid_dict(self):
        """
        Tests exception is thrown when params to payment_accepted don't have required key
        or have an bad value
        """
        baseline = {
            'orderNumber': '1',
            'orderCurrency': 'usd',
            'decision': 'ACCEPT',
        }
        wrong = {
            'orderNumber': 'k',
        }
        # tests for missing key
        for key in baseline:
            params = baseline.copy()
            del params[key]
            with self.assertRaises(CCProcessorDataException):
                payment_accepted(params)

        # tests for keys with value that can't be converted to proper type
        for key in wrong:
            params = baseline.copy()
            params[key] = wrong[key]
            with self.assertRaises(CCProcessorDataException):
                payment_accepted(params)

    def test_payment_accepted_order(self):
        """
        Tests payment_accepted cases with an order
        """
        student1 = UserFactory()
        student1.save()

        order1 = Order.get_cart_for_user(student1)
        params = {
            'card_accountNumber': '1234',
            'card_cardType': '001',
            'billTo_firstName': student1.first_name,
            'billTo_lastName': u"\u2603",
            'orderNumber': str(order1.id),
            'orderCurrency': 'usd',
            'decision': 'ACCEPT',
            'ccAuthReply_amount': '0.00'
        }

        # tests for an order number that doesn't match up
        params_bad_ordernum = params.copy()
        params_bad_ordernum['orderNumber'] = str(order1.id + 10)
        with self.assertRaises(CCProcessorDataException):
            payment_accepted(params_bad_ordernum)

        # tests for a reply amount of the wrong type
        params_wrong_type_amt = params.copy()
        params_wrong_type_amt['ccAuthReply_amount'] = 'ab'
        with self.assertRaises(CCProcessorDataException):
            payment_accepted(params_wrong_type_amt)

        # tests for a reply amount of the wrong type
        params_wrong_amt = params.copy()
        params_wrong_amt['ccAuthReply_amount'] = '1.00'
        with self.assertRaises(CCProcessorWrongAmountException):
            payment_accepted(params_wrong_amt)

        # tests for a not accepted order
        params_not_accepted = params.copy()
        params_not_accepted['decision'] = "REJECT"
        self.assertFalse(payment_accepted(params_not_accepted)['accepted'])

        # finally, tests an accepted order
        self.assertTrue(payment_accepted(params)['accepted'])

    @patch('shoppingcart.processors.CyberSource.render_to_string', autospec=True)
    def test_render_purchase_form_html(self, render):
        """
        Tests the rendering of the purchase form
        """
        student1 = UserFactory()
        student1.save()

        order1 = Order.get_cart_for_user(student1)
        item1 = OrderItem(order=order1, user=student1, unit_cost=1.0, line_cost=1.0)
        item1.save()
        render_purchase_form_html(order1)
        ((template, context), render_kwargs) = render.call_args

        self.assertEqual(template, 'shoppingcart/cybersource_form.html')
        self.assertDictContainsSubset({'amount': '1.00',
                                       'currency': 'usd',
                                       'orderPage_transactionType': 'sale',
                                       'orderNumber': str(order1.id)},
                                      context['params'])

    def test_process_postpay_exception(self):
        """
        Tests the exception path of process_postpay_callback
        """
        baseline = {
            'orderNumber': '1',
            'orderCurrency': 'usd',
            'decision': 'ACCEPT',
        }
        # tests for missing key
        for key in baseline:
            params = baseline.copy()
            del params[key]
            result = process_postpay_callback(params)
            self.assertFalse(result['success'])
            self.assertIsNone(result['order'])
            self.assertIn('error_msg', result['error_html'])

    @patch('shoppingcart.processors.CyberSource.verify_signatures', Mock(return_value=True))
    def test_process_postpay_accepted(self):
        """
        Tests the ACCEPTED path of process_postpay
        """
        student1 = UserFactory()
        student1.save()

        order1 = Order.get_cart_for_user(student1)
        params = {
            'card_accountNumber': '1234',
            'card_cardType': '001',
            'billTo_firstName': student1.first_name,
            'orderNumber': str(order1.id),
            'orderCurrency': 'usd',
            'decision': 'ACCEPT',
            'ccAuthReply_amount': '0.00'
        }
        result = process_postpay_callback(params)
        self.assertTrue(result['success'])
        self.assertEqual(result['order'], order1)
        order1 = Order.objects.get(id=order1.id)  # reload from DB to capture side-effect of process_postpay_callback
        self.assertEqual(order1.status, 'purchased')
        self.assertFalse(result['error_html'])

    @patch('shoppingcart.processors.CyberSource.verify_signatures', Mock(return_value=True))
    def test_process_postpay_not_accepted(self):
        """
        Tests the non-ACCEPTED path of process_postpay
        """
        student1 = UserFactory()
        student1.save()

        order1 = Order.get_cart_for_user(student1)
        params = {
            'card_accountNumber': '1234',
            'card_cardType': '001',
            'billTo_firstName': student1.first_name,
            'orderNumber': str(order1.id),
            'orderCurrency': 'usd',
            'decision': 'REJECT',
            'ccAuthReply_amount': '0.00',
            'reasonCode': '207'
        }
        result = process_postpay_callback(params)
        self.assertFalse(result['success'])
        self.assertEqual(result['order'], order1)
        self.assertEqual(order1.status, 'cart')
        self.assertIn(REASONCODE_MAP['207'], result['error_html'])
