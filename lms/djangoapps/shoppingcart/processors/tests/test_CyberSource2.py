# -*- coding: utf-8 -*-
"""
Tests for the newer CyberSource API implementation.
"""
from mock import patch
from django.test import TestCase
import ddt

from student.tests.factories import UserFactory
from shoppingcart.models import Order, OrderItem
from shoppingcart.processors.CyberSource2 import (
    processor_hash,
    process_postpay_callback,
    render_purchase_form_html,
    get_signed_purchase_params
)


@ddt.ddt
class CyberSource2Test(TestCase):
    """
    Test the CyberSource API implementation.  As much as possible,
    this test case should use ONLY the public processor interface
    (defined in shoppingcart.processors.__init__.py).

    Some of the tests in this suite rely on Django settings
    to be configured a certain way.

    """

    COST = "10.00"
    CALLBACK_URL = "/test_callback_url"

    def setUp(self):
        """ Create a user and an order. """
        self.user = UserFactory()
        self.order = Order.get_cart_for_user(self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            user=self.user,
            unit_cost=self.COST,
            line_cost=self.COST
        )

    def test_render_purchase_form_html(self):
        # Verify that the HTML form renders with the payment URL specified
        # in the test settings.
        # This does NOT test that all the form parameters are correct;
        # we verify that by testing `get_signed_purchase_params()` directly.
        html = render_purchase_form_html(self.order, callback_url=self.CALLBACK_URL)
        self.assertIn('<form action="/shoppingcart/payment_fake" method="post">', html)
        self.assertIn('transaction_uuid', html)
        self.assertIn('signature', html)
        self.assertIn(self.CALLBACK_URL, html)

    def test_get_signed_purchase_params(self):
        params = get_signed_purchase_params(self.order, callback_url=self.CALLBACK_URL)

        # Check the callback URL override
        self.assertEqual(params['override_custom_receipt_page'], self.CALLBACK_URL)

        # Parameters determined by the order model
        self.assertEqual(params['amount'], '10.00')
        self.assertEqual(params['currency'], 'usd')
        self.assertEqual(params['orderNumber'], 'OrderId: {order_id}'.format(order_id=self.order.id))
        self.assertEqual(params['reference_number'], self.order.id)

        # Parameters determined by the Django (test) settings
        self.assertEqual(params['access_key'], '0123456789012345678901')
        self.assertEqual(params['profile_id'], 'edx')

        # Some fields will change depending on when the test runs,
        # so we just check that they're set to a non-empty string
        self.assertGreater(len(params['signed_date_time']), 0)
        self.assertGreater(len(params['transaction_uuid']), 0)

        # Constant parameters
        self.assertEqual(params['transaction_type'], 'sale')
        self.assertEqual(params['locale'], 'en')
        self.assertEqual(params['payment_method'], 'card')
        self.assertEqual(
            params['signed_field_names'],
            ",".join([
                'amount',
                'currency',
                'orderNumber',
                'access_key',
                'profile_id',
                'reference_number',
                'transaction_type',
                'locale',
                'signed_date_time',
                'signed_field_names',
                'unsigned_field_names',
                'transaction_uuid',
                'payment_method',
                'override_custom_receipt_page',
                'override_custom_cancel_page',
            ])
        )
        self.assertEqual(params['unsigned_field_names'], '')

        # Check the signature
        self.assertEqual(params['signature'], self._signature(params))

    # We patch the purchased callback because
    # (a) we're using the OrderItem base class, which doesn't implement this method, and
    # (b) we want to verify that the method gets called on success.
    @patch.object(OrderItem, 'purchased_callback')
    def test_process_payment_success(self, purchased_callback):
        # Simulate a callback from CyberSource indicating that payment was successful
        params = self._signed_callback_params(self.order.id, self.COST, self.COST)
        result = process_postpay_callback(params)

        # Expect that we processed the payment successfully
        self.assertTrue(
            result['success'],
            msg="Payment was not successful: {error}".format(error=result.get('error_html'))
        )
        self.assertEqual(result['error_html'], '')

        # Expect that the item's purchased callback was invoked
        purchased_callback.assert_called_with()

        # Expect that the order has been marked as purchased
        self.assertEqual(result['order'].status, 'purchased')

    def test_process_payment_rejected(self):
        # Simulate a callback from CyberSource indicating that the payment was rejected
        params = self._signed_callback_params(self.order.id, self.COST, self.COST, accepted=False)
        result = process_postpay_callback(params)

        # Expect that we get an error message
        self.assertFalse(result['success'])
        self.assertIn(u"did not accept your payment", result['error_html'])

    def test_process_payment_invalid_signature(self):
        # Simulate a callback from CyberSource indicating that the payment was rejected
        params = self._signed_callback_params(self.order.id, self.COST, self.COST, signature="invalid!")
        result = process_postpay_callback(params)

        # Expect that we get an error message
        self.assertFalse(result['success'])
        self.assertIn(u"corrupted message regarding your charge", result['error_html'])

    def test_process_payment_invalid_order(self):
        # Use an invalid order ID
        params = self._signed_callback_params("98272", self.COST, self.COST)
        result = process_postpay_callback(params)

        # Expect an error
        self.assertFalse(result['success'])
        self.assertIn(u"inconsistent data", result['error_html'])

    def test_process_invalid_payment_amount(self):
        # Change the payment amount (no longer matches the database order record)
        params = self._signed_callback_params(self.order.id, "145.00", "145.00")
        result = process_postpay_callback(params)

        # Expect an error
        self.assertFalse(result['success'])
        self.assertIn(u"different amount than the order total", result['error_html'])

    def test_process_amount_paid_not_decimal(self):
        # Change the payment amount to a non-decimal
        params = self._signed_callback_params(self.order.id, self.COST, "abcd")
        result = process_postpay_callback(params)

        # Expect an error
        self.assertFalse(result['success'])
        self.assertIn(u"badly-typed value", result['error_html'])

    def test_process_user_cancelled(self):
        # Change the payment amount to a non-decimal
        params = self._signed_callback_params(self.order.id, self.COST, "abcd")
        params['decision'] = u'CANCEL'
        result = process_postpay_callback(params)

        # Expect an error
        self.assertFalse(result['success'])
        self.assertIn(u"you have cancelled this transaction", result['error_html'])

    @patch.object(OrderItem, 'purchased_callback')
    def test_process_no_credit_card_digits(self, callback):
        # Use a credit card number with no digits provided
        params = self._signed_callback_params(
            self.order.id, self.COST, self.COST,
            card_number='nodigits'
        )
        result = process_postpay_callback(params)

        # Expect that we processed the payment successfully
        self.assertTrue(
            result['success'],
            msg="Payment was not successful: {error}".format(error=result.get('error_html'))
        )
        self.assertEqual(result['error_html'], '')

        # Expect that the order has placeholders for the missing credit card digits
        self.assertEqual(result['order'].bill_to_ccnum, '####')

    @ddt.data('req_reference_number', 'req_currency', 'decision', 'auth_amount')
    def test_process_missing_parameters(self, missing_param):
        # Remove a required parameter
        params = self._signed_callback_params(self.order.id, self.COST, self.COST)
        del params[missing_param]

        # Recalculate the signature with no signed fields so we can get past
        # signature validation.
        params['signed_field_names'] = 'reason_code,message'
        params['signature'] = self._signature(params)

        result = process_postpay_callback(params)

        # Expect an error
        self.assertFalse(result['success'])
        self.assertIn(u"did not return a required parameter", result['error_html'])

    @patch.object(OrderItem, 'purchased_callback')
    def test_sign_then_verify_unicode(self, purchased_callback):
        params = self._signed_callback_params(
            self.order.id, self.COST, self.COST,
            first_name=u'\u2699'
        )

        # Verify that this executes without a unicode error
        result = process_postpay_callback(params)
        self.assertTrue(result['success'])

    def _signed_callback_params(
        self, order_id, order_amount, paid_amount,
        accepted=True, signature=None, card_number='xxxxxxxxxxxx1111',
        first_name='John'
    ):
        """
        Construct parameters that could be returned from CyberSource
        to our payment callback.

        Some values can be overridden to simulate different test scenarios,
        but most are fake values captured from interactions with
        a CyberSource test account.

        Args:
            order_id (string or int): The ID of the `Order` model.
            order_amount (string): The cost of the order.
            paid_amount (string): The amount the user paid using CyberSource.

        Keyword Args:

            accepted (bool): Whether the payment was accepted or rejected.
            signature (string): If provided, use this value instead of calculating the signature.
            card_numer (string): If provided, use this value instead of the default credit card number.
            first_name (string): If provided, the first name of the user.

        Returns:
            dict

        """
        # Parameters sent from CyberSource to our callback implementation
        # These were captured from the CC test server.
        params = {
            # Parameters that change based on the test
            "decision": "ACCEPT" if accepted else "REJECT",
            "req_reference_number": str(order_id),
            "req_amount": order_amount,
            "auth_amount": paid_amount,
            "req_card_number": card_number,

            # Stub values
            "utf8": u"✓",
            "req_bill_to_address_country": "US",
            "auth_avs_code": "X",
            "req_card_expiry_date": "01-2018",
            "bill_trans_ref_no": "85080648RYI23S6I",
            "req_bill_to_address_state": "MA",
            "signed_field_names": ",".join([
                "transaction_id",
                "decision",
                "req_access_key",
                "req_profile_id",
                "req_transaction_uuid",
                "req_transaction_type",
                "req_reference_number",
                "req_amount",
                "req_currency",
                "req_locale",
                "req_payment_method",
                "req_override_custom_receipt_page",
                "req_bill_to_forename",
                "req_bill_to_surname",
                "req_bill_to_email",
                "req_bill_to_address_line1",
                "req_bill_to_address_city",
                "req_bill_to_address_state",
                "req_bill_to_address_country",
                "req_bill_to_address_postal_code",
                "req_card_number",
                "req_card_type",
                "req_card_expiry_date",
                "message",
                "reason_code",
                "auth_avs_code",
                "auth_avs_code_raw",
                "auth_response",
                "auth_amount",
                "auth_code",
                "auth_trans_ref_no",
                "auth_time",
                "bill_trans_ref_no",
                "signed_field_names",
                "signed_date_time"
            ]),
            "req_payment_method": "card",
            "req_transaction_type": "sale",
            "auth_code": "888888",
            "req_locale": "en",
            "reason_code": "100",
            "req_bill_to_address_postal_code": "02139",
            "req_bill_to_address_line1": "123 Fake Street",
            "req_card_type": "001",
            "req_bill_to_address_city": "Boston",
            "signed_date_time": "2014-08-18T14:07:10Z",
            "req_currency": "usd",
            "auth_avs_code_raw": "I1",
            "transaction_id": "4083708299660176195663",
            "auth_time": "2014-08-18T140710Z",
            "message": "Request was processed successfully.",
            "auth_response": "100",
            "req_profile_id": "0000001",
            "req_transaction_uuid": "ddd9935b82dd403f9aa4ba6ecf021b1f",
            "auth_trans_ref_no": "85080648RYI23S6I",
            "req_bill_to_surname": "Doe",
            "req_bill_to_forename": first_name,
            "req_bill_to_email": "john@example.com",
            "req_override_custom_receipt_page": "http://localhost:8000/shoppingcart/postpay_callback/",
            "req_access_key": "abcd12345",
        }

        # Calculate the signature
        params['signature'] = signature if signature is not None else self._signature(params)
        return params

    def _signature(self, params):
        """
        Calculate the signature from a dictionary of params.

        NOTE: This method uses the processor's hashing method.  That method
        is a thin wrapper of standard library calls, and it seemed overly complex
        to rewrite that code in the test suite.

        Args:
            params (dict): Dictionary with a key 'signed_field_names',
                which is a comma-separated list of keys in the dictionary
                to include in the signature.

        Returns:
            string

        """
        return processor_hash(
            ",".join([
                u"{0}={1}".format(signed_field, params[signed_field])
                for signed_field
                in params['signed_field_names'].split(u",")
            ])
        )
