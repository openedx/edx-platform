# -*- coding: utf-8 -*-
"""
Tests for the newer CyberSource API implementation.
"""
import datetime
from mock import Mock, patch
from django.test import TestCase
from django.conf import settings
import ddt
from django.test.utils import override_settings
import pytz

from course_modes.models import CourseMode
from xmodule.modulestore.tests.factories import CourseFactory

from student.tests.factories import UserFactory

from shoppingcart.models import (
    Order,
    OrderItem,
    PaidCourseRegistration,
    PaymentTransaction,
    TRANSACTION_TYPE_PURCHASE,
    TRANSACTION_TYPE_REFUND
)

from shoppingcart.sync import perform_sync

from shoppingcart.processors.CyberSource2 import (
    processor_hash,
    process_postpay_callback,
    render_purchase_form_html,
    get_signed_purchase_params,
    _get_processor_exception_html,
    get_report_data_for_account,
    get_report_data,
    process_report_data,
)
from shoppingcart.processors.exceptions import (
    CCProcessorSignatureException,
    CCProcessorDataException,
    CCProcessorWrongAmountException
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
    FAILED_DECISIONS = ["DECLINE", "CANCEL", "ERROR"]

    def setUp(self):
        """ Create a user and an order. """
        super(CyberSource2Test, self).setUp()

        self.user = UserFactory()
        self.order = Order.get_cart_for_user(self.user)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            user=self.user,
            unit_cost=self.COST,
            line_cost=self.COST
        )

    def assert_dump_recorded(self, order):
        """
        Verify that this order does have a dump of information from the
        payment processor.
        """
        self.assertNotEqual(order.processor_reply_dump, '')

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
    # we're using the OrderItem base class, which throws an exception
    # when item doest not have a course id associated
    @patch.object(OrderItem, 'purchased_callback')
    def test_process_payment_raises_exception(self, purchased_callback):  # pylint: disable=unused-argument
        self.order.clear()
        OrderItem.objects.create(
            order=self.order,
            user=self.user,
            unit_cost=self.COST,
            line_cost=self.COST,
        )
        params = self._signed_callback_params(self.order.id, self.COST, self.COST)
        process_postpay_callback(params)

    # We patch the purchased callback because
    # (a) we're using the OrderItem base class, which doesn't implement this method, and
    # (b) we want to verify that the method gets called on success.
    @patch.object(OrderItem, 'purchased_callback')
    @patch.object(OrderItem, 'pdf_receipt_display_name')
    def test_process_payment_success(self, pdf_receipt_display_name, purchased_callback):  # pylint: disable=unused-argument
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
        self.assert_dump_recorded(result['order'])

    def test_process_payment_rejected(self):
        # Simulate a callback from CyberSource indicating that the payment was rejected
        params = self._signed_callback_params(self.order.id, self.COST, self.COST, decision='REJECT')
        result = process_postpay_callback(params)

        # Expect that we get an error message
        self.assertFalse(result['success'])
        self.assertIn(u"did not accept your payment", result['error_html'])
        self.assert_dump_recorded(result['order'])

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
        # refresh data for current order
        order = Order.objects.get(id=self.order.id)
        self.assert_dump_recorded(order)

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
    @patch.object(OrderItem, 'pdf_receipt_display_name')
    def test_process_no_credit_card_digits(self, pdf_receipt_display_name, purchased_callback):  # pylint: disable=unused-argument
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
        self.assert_dump_recorded(result['order'])

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
    @patch.object(OrderItem, 'pdf_receipt_display_name')
    def test_sign_then_verify_unicode(self, pdf_receipt_display_name, purchased_callback):  # pylint: disable=unused-argument
        params = self._signed_callback_params(
            self.order.id, self.COST, self.COST,
            first_name=u'\u2699'
        )

        # Verify that this executes without a unicode error
        result = process_postpay_callback(params)
        self.assertTrue(result['success'])
        self.assert_dump_recorded(result['order'])

    @ddt.data('string', u'üñîçø∂é')
    def test_get_processor_exception_html(self, error_string):
        """
        Tests the processor exception html message
        """
        for exception_type in [CCProcessorSignatureException, CCProcessorWrongAmountException, CCProcessorDataException]:
            error_msg = error_string
            exception = exception_type(error_msg)
            html = _get_processor_exception_html(exception)
            self.assertIn(settings.PAYMENT_SUPPORT_EMAIL, html)
            self.assertIn('Sorry!', html)
            self.assertIn(error_msg, html)

    def _signed_callback_params(
        self, order_id, order_amount, paid_amount,
        decision='ACCEPT', signature=None, card_number='xxxxxxxxxxxx1111',
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

            decision (string): Whether the payment was accepted or rejected or declined.
            signature (string): If provided, use this value instead of calculating the signature.
            card_numer (string): If provided, use this value instead of the default credit card number.
            first_name (string): If provided, the first name of the user.

        Returns:
            dict

        """
        # Parameters sent from CyberSource to our callback implementation
        # These were captured from the CC test server.

        signed_field_names = ["transaction_id",
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
                              "signed_date_time"]

        # if decision is in FAILED_DECISIONS list then remove  auth_amount from
        # signed_field_names list.
        if decision in self.FAILED_DECISIONS:
            signed_field_names.remove("auth_amount")

        params = {
            # Parameters that change based on the test
            "decision": decision,
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
            "signed_field_names": ",".join(signed_field_names),
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

        # if decision is in FAILED_DECISIONS list then remove the auth_amount from params dict

        if decision in self.FAILED_DECISIONS:
            del params["auth_amount"]

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

    def test_process_payment_declined(self):
        # Simulate a callback from CyberSource indicating that the payment was declined
        params = self._signed_callback_params(self.order.id, self.COST, self.COST, decision='DECLINE')
        result = process_postpay_callback(params)

        # Expect that we get an error message
        self.assertFalse(result['success'])
        self.assertIn(u"payment was declined", result['error_html'])

    MOCKED_REPORT_CSV_CONTENT = """header\n
        batch_id,merchant_id, batch_date,request_id,merchant_ref_number,trans_ref_no,payment_method,currency,amount,transaction_type\n
        1, foo_account, 01/01/15, 1, 1, 1, Visa, USD, 10, ics_bill\n
        2, foo_account, 01/01/15, 1, 2, 2, Visa, USD, 20.50, ics_bill\n
        3, foo_account, 01/01/15, 1, 3, 3, Visa, USD, 60, ics_bill\n
        4, foo_account, 01/01/15, 1, 1, 4, Visa, USD, 10, ics_credit"""

    def test_get_report_data_for_account(self):
        """
        This test mocks out the CyberSource PaymentBatchDetailReport and see if it operates as expected
        """

        with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = self.MOCKED_REPORT_CSV_CONTENT

            data = get_report_data_for_account(
                'foo_account',
                {
                    'REPORTING_BASE_ENDPOINT': 'https://rogus.mcbogus.com/',
                    'REPORTING_AUTH_USERNAME': 'foo',
                    'REPORTING_AUTH_PASSWORD': 'bar',
                },
                datetime.datetime.now(pytz.UTC) - datetime.timedelta(1)
            )

            self.assertEqual(len(data), 4)

    TEST_REPORTING_CC_PROCESSOR_NAME = "CyberSource2"
    TEST_REPORTING_CC_PROCESSOR = {
        'CyberSource2': {
            "REPORTING_BASE_ENDPOINT": "dummy",
            "REPORTING_ACCOUNT_NAME": "first",
            "REPORTING_AUTH_USERNAME": "dummy",
            "REPORTING_AUTH_PASSWORD": "dummy",
        }
    }
    TEST_REPORTING_CC_PROCESSOR_MICROSITES = {
        'CyberSource2': {
            "REPORTING_BASE_ENDPOINT": "dummy",
            "REPORTING_ACCOUNT_NAME": "first",
            "REPORTING_AUTH_USERNAME": "dummy",
            "REPORTING_AUTH_PASSWORD": "dummy",
            "microsites": {
                'foo': {
                    "REPORTING_BASE_ENDPOINT": "dummy",
                    "REPORTING_ACCOUNT_NAME": "second",
                    "REPORTING_AUTH_USERNAME": "dummy",
                    "REPORTING_AUTH_PASSWORD": "dummy",
                },
                'bar': {
                    "REPORTING_BASE_ENDPOINT": "dummy",
                    # intentionally have two microsites that point
                    # to the same account_name
                    "REPORTING_ACCOUNT_NAME": "second",
                    "REPORTING_AUTH_USERNAME": "dummy",
                    "REPORTING_AUTH_PASSWORD": "dummy",
                },
                'baz': {
                    # leave an empty one to make sure we skip it
                },
            }
        }
    }

    @override_settings(
        CC_PROCESSOR_NAME=TEST_REPORTING_CC_PROCESSOR_NAME,
        CC_PROCESSOR=TEST_REPORTING_CC_PROCESSOR_MICROSITES
    )
    def test_get_report_data(self):
        """
        This verifies getting report data over all accounts defined in the configuration
        """

        with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = self.MOCKED_REPORT_CSV_CONTENT

            data = get_report_data(datetime.datetime.now(pytz.UTC) - datetime.timedelta(1))

            # this should be 8 because we are fetching the same mocked out data twice
            # once for the root and the other for a microsite. Note there are two
            # microsites, but they are defined to use the same account (so it shouldn'e be 12)
            self.assertEqual(len(data), 8)

    def test_process_report_data_no_orders(self):
        """
        This will verify processing data that contains errors (missing Orders)
        """

        test_data = [
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': '1000',
                'currency': 'USD',
                'amount': '100',
                'transaction_type': 'ics_bill',
                'trans_ref_no': '100',
            },
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': '1001',
                'currency': 'USD',
                'amount': '20.50',
                'transaction_type': 'ics_bill',
                'trans_ref_no': '101',
            },
        ]

        num_processed, num_in_err, errors = process_report_data(test_data)

        # since none of the OrderId's can be found, they should all be counted as errors
        self.assertEqual(num_processed, 0)
        self.assertEqual(num_in_err, 2)
        self.assertEqual(len(errors), 2)

    def _set_up_purchased_order(self, cost=40):
        """
        This is a helper method to set up a course with a price and purchase it
        """

        user = UserFactory.create()

        course = CourseFactory.create()
        course_key = course.id
        course_mode = CourseMode(
            course_id=course_key,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=cost
        )
        course_mode.save()

        order = Order.get_cart_for_user(user)
        PaidCourseRegistration.add_to_order(order, course_key)
        order.purchase()

        return order, course

    def test_process_report_data_with_orders(self):
        """
        This will verify processing data that has corresponding Orders
        """

        order, course = self._set_up_purchased_order()
        order2, course2 = self._set_up_purchased_order(100)

        test_data = [
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(order.total_cost),
                'transaction_type': 'ics_bill',
                'trans_ref_no': '100',
            },
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(-order.total_cost),
                'transaction_type': 'ics_credit',
                'trans_ref_no': '101',
            },
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order2.id),
                'currency': 'USD',
                'amount': str(order2.total_cost),
                'transaction_type': 'ics_bill',
                'trans_ref_no': '102',
            },
        ]

        num_processed, num_in_err, errors = process_report_data(test_data)

        # since none of the OrderId's can be found, they should all be counted as errors
        self.assertEqual(num_processed, 3)
        self.assertEqual(num_in_err, 0)
        self.assertEqual(len(errors), 0)

        # verify that we have saved PaymentTransactions
        self.assertEqual(len(PaymentTransaction.objects.all()), 3)

        trans = PaymentTransaction.get_by_remote_transaction_id('100')
        self.assertEqual(trans.transaction_type, TRANSACTION_TYPE_PURCHASE)
        self.assertEqual(trans.account_id, 'foo')
        self.assertEqual(trans.order.id, order.id)
        self.assertEqual(trans.currency, 'USD')
        self.assertEqual(trans.amount, order.total_cost)
        self.assertEqual(trans.processed_at, datetime.datetime(2015, 1, 2, tzinfo=pytz.UTC))

        trans = PaymentTransaction.get_by_remote_transaction_id('101')
        self.assertEqual(trans.transaction_type, TRANSACTION_TYPE_REFUND)

        # now verify that we have transaction to course mappings
        course_transactions = PaymentTransaction.get_transactions_for_course(course.id)
        self.assertEqual(len(course_transactions.all()), 2)

        course_transactions = PaymentTransaction.get_transactions_for_course(course2.id)
        self.assertEqual(len(course_transactions.all()), 1)

        # very that transaction aggregations are as expected
        amounts = PaymentTransaction.get_transaction_totals_for_course(course.id)
        self.assertEqual(amounts['purchased'], order.total_cost)
        self.assertEqual(amounts['refunded'], -order.total_cost)

        amounts = PaymentTransaction.get_transaction_totals_for_course(course2.id)
        self.assertEqual(amounts['purchased'], order2.total_cost)
        self.assertEqual(amounts['refunded'], 0.0)

    def test_mismatched_totals(self):
        """
        This will verify that we will flag any transactions whose totals don't match up to the Invoice
        """

        order, __ = self._set_up_purchased_order()

        test_data = [
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(order.total_cost + 10),
                'transaction_type': 'ics_bill',
                'trans_ref_no': '100',
            },
        ]

        num_processed, num_in_err, errors = process_report_data(test_data)

        # since none of the OrderId's can be found, they should all be counted as errors
        self.assertEqual(num_processed, 0)
        self.assertEqual(num_in_err, 1)
        self.assertEqual(len(errors), 1)

    def test_mismatched_refund_totals(self):
        """
        This will verify that we will flag any refunds whose totals don't match up to the Invoice
        """

        order, __ = self._set_up_purchased_order()

        test_data = [
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(order.total_cost),
                'transaction_type': 'ics_bill',
                'trans_ref_no': '100',
            },
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(-order.total_cost + 10),
                'transaction_type': 'ics_credit',
                'trans_ref_no': '101',
            },
        ]

        num_processed, num_in_err, errors = process_report_data(test_data)

        # since none of the OrderId's can be found, they should all be counted as errors
        self.assertEqual(num_processed, 1)
        self.assertEqual(num_in_err, 1)
        self.assertEqual(len(errors), 1)

    def test_process_report_data_multi(self):
        """
        This will assert that the course mappings on an order which has multiple course_modes
        will properly spread out the sums
        """

        user = UserFactory.create()

        course = CourseFactory.create()
        course_mode = CourseMode(
            course_id=course.id,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=40
        )
        course_mode.save()

        course2 = CourseFactory.create()
        course_mode = CourseMode(
            course_id=course2.id,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=100
        )
        course_mode.save()

        order = Order.get_cart_for_user(user)
        PaidCourseRegistration.add_to_order(order, course.id)
        PaidCourseRegistration.add_to_order(order, course2.id)
        order.purchase()

        test_data = [
            {
                'merchant_id': 'foo',
                'batch_date': '1/2/15',
                'merchant_ref_number': str(order.id),
                'currency': 'USD',
                'amount': str(order.total_cost),
                'transaction_type': 'ics_bill',
                'trans_ref_no': '100',
            },
        ]

        num_processed, num_in_err, errors = process_report_data(test_data)

        # since none of the OrderId's can be found, they should all be counted as errors
        self.assertEqual(num_processed, 1)
        self.assertEqual(num_in_err, 0)
        self.assertEqual(len(errors), 0)

        # verify that we have saved PaymentTransactions
        self.assertEqual(len(PaymentTransaction.objects.all()), 1)

        # see that the aggregates are as expected
        # very that transaction aggregations are as expected
        amounts = PaymentTransaction.get_transaction_totals_for_course(course.id)
        self.assertEqual(amounts['purchased'], 40)
        self.assertEqual(amounts['refunded'], 0.0)

        amounts = PaymentTransaction.get_transaction_totals_for_course(course2.id)
        self.assertEqual(amounts['purchased'], 100)
        self.assertEqual(amounts['refunded'], 0.0)

    def _setup_purchases(self):
        """
        Helper method to set up some test information
        """
        user = UserFactory.create()

        course = CourseFactory.create()
        course_mode = CourseMode(
            course_id=course.id,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=40
        )
        course_mode.save()

        course2 = CourseFactory.create()
        course_mode = CourseMode(
            course_id=course2.id,
            mode_slug="honor",
            mode_display_name="honor cert",
            min_price=100
        )
        course_mode.save()

        order = Order.get_cart_for_user(user)
        PaidCourseRegistration.add_to_order(order, course.id)
        order.purchase()

        order2 = Order.get_cart_for_user(user)
        PaidCourseRegistration.add_to_order(order2, course2.id)
        order2.purchase()

        return order, order2, course, course2

    @override_settings(
        CC_PROCESSOR_NAME=TEST_REPORTING_CC_PROCESSOR_NAME,
        CC_PROCESSOR=TEST_REPORTING_CC_PROCESSOR
    )
    def test_perform_sync(self):
        """
        This verifies getting report data over all accounts defined in the configuration
        """

        order, order2, course, course2 = self._setup_purchases()

        test_csv_data = """header\n
        batch_id,merchant_id, batch_date,request_id,merchant_ref_number,trans_ref_no,payment_method,currency,amount,transaction_type\n
        1,foo_account,1/1/15,1,{order_id},1,Visa,USD,40,ics_bill\n
        2,foo_account,1/1/15,1,{order2_id},2,Visa,USD,100,ics_bill\n
        4,foo_account,1/1/15,1,{order_id},4,Visa,USD,-40,ics_credit""".format(
            order_id=order.id,
            order2_id=order2.id,
        )

        with patch('shoppingcart.sync.EmailMessage.send') as send_mail:
            with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
                mock_requests.get.return_value = mock_response = Mock()
                mock_response.status_code = 200
                mock_response.content = test_csv_data

                sync_op = perform_sync(summary_email_to='foo@bar.com')

                # make sure that the summary email was sent
                self.assertTrue(send_mail.called)

        self.assertEqual(sync_op.rows_processed, 3)
        self.assertEqual(sync_op.rows_in_error, 0)

        # see that the aggregates are as expected
        # very that transaction aggregations are as expected
        amounts = PaymentTransaction.get_transaction_totals_for_course(course.id)
        self.assertEqual(amounts['purchased'], 40)
        self.assertEqual(amounts['refunded'], -40.0)

        amounts = PaymentTransaction.get_transaction_totals_for_course(course2.id)
        self.assertEqual(amounts['purchased'], 100)
        self.assertEqual(amounts['refunded'], 0.0)

    @override_settings(
        CC_PROCESSOR_NAME=TEST_REPORTING_CC_PROCESSOR_NAME,
        CC_PROCESSOR=TEST_REPORTING_CC_PROCESSOR
    )
    def test_perform_sync_double(self):
        """
        This verifies getting report data over all accounts defined in the configuration
        """

        order, order2, course, course2 = self._setup_purchases()

        test_csv_data = """header\n
        batch_id,merchant_id, batch_date,request_id,merchant_ref_number,trans_ref_no,payment_method,currency,amount,transaction_type\n
        1,foo_account,1/1/15,1,{order_id},1,Visa,USD,40,ics_bill\n
        2,foo_account,1/1/15,1,{order2_id},2,Visa,USD,100,ics_bill\n
        4,foo_account,1/1/15,1,{order_id},4,Visa,USD,-40,ics_credit""".format(
            order_id=order.id,
            order2_id=order2.id,
        )

        with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = test_csv_data

            sync_op = perform_sync(
                datetime.datetime(2015, 1, 1, tzinfo=pytz.UTC),
                datetime.datetime(2015, 1, 2, tzinfo=pytz.UTC)
            )
            self.assertEqual(sync_op.rows_processed, 3)
            self.assertEqual(sync_op.rows_in_error, 0)

            sync_op = perform_sync(
                datetime.datetime(2015, 1, 1, tzinfo=pytz.UTC),
                datetime.datetime(2015, 1, 2, tzinfo=pytz.UTC)
            )
            self.assertEqual(sync_op.rows_processed, 3)
            self.assertEqual(sync_op.rows_in_error, 0)

        # verify that we don't have twice as many rows
        # even though we synced twice
        self.assertEqual(len(PaymentTransaction.objects.all()), 3)

        # see that the aggregates are as expected
        # very that transaction aggregations are as expected
        amounts = PaymentTransaction.get_transaction_totals_for_course(course.id)
        self.assertEqual(amounts['purchased'], 40)
        self.assertEqual(amounts['refunded'], -40.0)

        amounts = PaymentTransaction.get_transaction_totals_for_course(course2.id)
        self.assertEqual(amounts['purchased'], 100)
        self.assertEqual(amounts['refunded'], 0.0)

    @override_settings(
        CC_PROCESSOR_NAME=TEST_REPORTING_CC_PROCESSOR_NAME,
        CC_PROCESSOR=TEST_REPORTING_CC_PROCESSOR
    )
    def test_perform_sync_missing_order(self):
        """
        This verifies getting report data over all accounts defined in the configuration
        """

        order, order2, __, ___ = self._setup_purchases()

        test_csv_data = """header\n
        batch_id,merchant_id, batch_date,request_id,merchant_ref_number,trans_ref_no,payment_method,currency,amount,transaction_type\n
        1,foo_account,1/1/15,1,{order_id},1,Visa,USD,40,ics_bill\n
        2,foo_account,1/1/15,1,{order2_id},2,Visa,USD,100,ics_bill\n
        4,foo_account,1/1/15,1,0,3,Visa,USD,100,ics_bill""".format(
            order_id=order.id,
            order2_id=order2.id,
        )

        with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
            print
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = test_csv_data

            sync_op = perform_sync()

        self.assertEqual(sync_op.rows_processed, 2)
        self.assertEqual(sync_op.rows_in_error, 1)

    @override_settings(
        CC_PROCESSOR_NAME=TEST_REPORTING_CC_PROCESSOR_NAME,
        CC_PROCESSOR=TEST_REPORTING_CC_PROCESSOR
    )
    def test_perform_sync_unpurchased(self):
        """
        This verifies getting report data over all accounts defined in the configuration
        """
        __, ___, course, ____ = self._setup_purchases()

        user = UserFactory.create()
        order3 = Order.get_cart_for_user(user)
        PaidCourseRegistration.add_to_order(order3, course.id)

        test_csv_data = """header\n
        batch_id,merchant_id, batch_date,request_id,merchant_ref_number,trans_ref_no,payment_method,currency,amount,transaction_type\n
        1,foo_account,1/1/15,1,{order_id},1,Visa,USD,40,ics_bill\n""".format(
            order_id=order3.id,
        )

        with patch('shoppingcart.processors.CyberSource2.requests') as mock_requests:
            print
            mock_requests.get.return_value = mock_response = Mock()
            mock_response.status_code = 200
            mock_response.content = test_csv_data

            sync_op = perform_sync()

        self.assertEqual(sync_op.rows_processed, 0)
        self.assertEqual(sync_op.rows_in_error, 1)
