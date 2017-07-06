"""
Tests for the fake payment page used in acceptance tests.
"""

from django.test import TestCase
from shoppingcart.processors.CyberSource2 import sign, verify_signatures
from shoppingcart.processors.exceptions import CCProcessorSignatureException
from shoppingcart.tests.payment_fake import PaymentFakeView
from collections import OrderedDict


class PaymentFakeViewTest(TestCase):
    """
    Test that the fake payment view interacts
    correctly with the shopping cart.
    """

    def setUp(self):
        super(PaymentFakeViewTest, self).setUp()

        # Reset the view state
        PaymentFakeView.PAYMENT_STATUS_RESPONSE = "success"

        self.client_post_params = OrderedDict([
            ('amount', '25.00'),
            ('currency', 'usd'),
            ('transaction_type', 'sale'),
            ('orderNumber', '33'),
            ('access_key', '123456789'),
            ('merchantID', 'edx'),
            ('djch', '012345678912'),
            ('orderPage_version', 2),
            ('orderPage_serialNumber', '1234567890'),
            ('profile_id', "00000001"),
            ('reference_number', 10),
            ('locale', 'en'),
            ('signed_date_time', '2014-08-18T13:59:31Z'),
        ])

    def test_accepts_client_signatures(self):

        # Generate shoppingcart signatures
        post_params = sign(self.client_post_params)

        # Simulate a POST request from the payment workflow
        # page to the fake payment page.
        resp = self.client.post(
            '/shoppingcart/payment_fake', dict(post_params)
        )

        # Expect that the response was successful
        self.assertEqual(resp.status_code, 200)

        # Expect that we were served the payment page
        # (not the error page)
        self.assertIn("Payment Form", resp.content)

    def test_rejects_invalid_signature(self):

        # Generate shoppingcart signatures
        post_params = sign(self.client_post_params)

        # Tamper with the signature
        post_params['signature'] = "invalid"

        # Simulate a POST request from the payment workflow
        # page to the fake payment page.
        resp = self.client.post(
            '/shoppingcart/payment_fake', dict(post_params)
        )

        # Expect that we got an error
        self.assertIn("Error", resp.content)

    def test_sends_valid_signature(self):

        # Generate shoppingcart signatures
        post_params = sign(self.client_post_params)

        # Get the POST params that the view would send back to us
        resp_params = PaymentFakeView.response_post_params(post_params)

        # Check that the client accepts these
        try:
            verify_signatures(resp_params)

        except CCProcessorSignatureException:
            self.fail("Client rejected signatures.")

    def test_set_payment_status(self):

        # Generate shoppingcart signatures
        post_params = sign(self.client_post_params)

        # Configure the view to declined payments
        resp = self.client.put(
            '/shoppingcart/payment_fake',
            data="decline", content_type='text/plain'
        )
        self.assertEqual(resp.status_code, 200)

        # Check that the decision is "DECLINE"
        resp_params = PaymentFakeView.response_post_params(post_params)
        self.assertEqual(resp_params.get('decision'), 'DECLINE')

        # Configure the view to fail payments
        resp = self.client.put(
            '/shoppingcart/payment_fake',
            data="failure", content_type='text/plain'
        )
        self.assertEqual(resp.status_code, 200)

        # Check that the decision is "REJECT"
        resp_params = PaymentFakeView.response_post_params(post_params)
        self.assertEqual(resp_params.get('decision'), 'REJECT')

        # Configure the view to accept payments
        resp = self.client.put(
            '/shoppingcart/payment_fake',
            data="success", content_type='text/plain'
        )
        self.assertEqual(resp.status_code, 200)

        # Check that the decision is "ACCEPT"
        resp_params = PaymentFakeView.response_post_params(post_params)
        self.assertEqual(resp_params.get('decision'), 'ACCEPT')
