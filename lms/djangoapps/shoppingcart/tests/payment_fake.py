# -*- coding: utf-8 -*-
"""
Fake payment page for use in acceptance tests.
This view is enabled in the URLs by the feature flag `ENABLE_PAYMENT_FAKE`.

Note that you will still need to configure this view as the payment
processor endpoint in order for the shopping cart to use it:

    settings.CC_PROCESSOR['CyberSource']['PURCHASE_ENDPOINT'] = "/shoppingcart/payment_fake"

You can configure the payment to indicate success or failure by sending a PUT
request to the view with param "success"
set to "success" or "failure".  The view defaults to payment success.
"""

from django.views.generic.base import View
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest
from edxmako.shortcuts import render_to_response


# We use the same hashing function as the software under test,
# because it mainly uses standard libraries, and I want
# to avoid duplicating that code.
from shoppingcart.processors.CyberSource2 import processor_hash


class PaymentFakeView(View):
    """
    Fake payment page for use in acceptance tests.
    """

    # We store the payment status to respond with in a class
    # variable.  In a multi-process Django app, this wouldn't work,
    # since processes don't share memory.  Since Lettuce
    # runs one Django server process, this works for acceptance testing.
    PAYMENT_STATUS_RESPONSE = "success"

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        """
        Disable CSRF for these methods.
        """
        return super(PaymentFakeView, self).dispatch(*args, **kwargs)

    def post(self, request):
        """
        Render a fake payment page.

        This is an HTML form that:

        * Triggers a POST to `postpay_callback()` on submit.

        * Has hidden fields for all the data CyberSource sends to the callback.
            - Most of this data is duplicated from the request POST params (e.g. `amount`)
            - Other params contain fake data (always the same user name and address.
            - Still other params are calculated (signatures)

        * Serves an error page (HTML) with a 200 status code
          if the signatures are invalid.  This is what CyberSource does.

        Since all the POST requests are triggered by HTML forms, this is
        equivalent to the CyberSource payment page, even though it's
        served by the shopping cart app.
        """
        if self._is_signature_valid(request.POST):
            return self._payment_page_response(request.POST)

        else:
            return render_to_response('shoppingcart/test/fake_payment_error.html')

    def put(self, request):
        """
        Set the status of payment requests to success or failure.

        Accepts one POST param "status" that can be either "success"
        or "failure".
        """
        new_status = request.body

        if new_status not in ["success", "failure", "decline"]:
            return HttpResponseBadRequest()

        else:
            # Configure all views to respond with the new status
            PaymentFakeView.PAYMENT_STATUS_RESPONSE = new_status
            return HttpResponse()

    @staticmethod
    def _is_signature_valid(post_params):
        """
        Return a bool indicating  whether the client sent
        us a valid signature in the payment page request.
        """
        # Retrieve the list of signed fields
        signed_fields = post_params.get('signed_field_names').split(',')

        # Calculate the public signature
        hash_val = ",".join([
            u"{0}={1}".format(key, post_params[key])
            for key in signed_fields
        ])
        public_sig = processor_hash(hash_val)

        return public_sig == post_params.get('signature')

    @classmethod
    def response_post_params(cls, post_params):
        """
        Calculate the POST params we want to send back to the client.
        """

        if cls.PAYMENT_STATUS_RESPONSE == "success":
            decision = "ACCEPT"
        elif cls.PAYMENT_STATUS_RESPONSE == "decline":
            decision = "DECLINE"
        else:
            decision = "REJECT"

        resp_params = {
            # Indicate whether the payment was successful
            "decision": decision,

            # Reflect back parameters we were sent by the client
            "req_amount": post_params.get('amount'),
            "auth_amount": post_params.get('amount'),
            "req_reference_number": post_params.get('reference_number'),
            "req_transaction_uuid": post_params.get('transaction_uuid'),
            "req_access_key": post_params.get('access_key'),
            "req_transaction_type": post_params.get('transaction_type'),
            "req_override_custom_receipt_page": post_params.get('override_custom_receipt_page'),
            "req_payment_method": post_params.get('payment_method'),
            "req_currency": post_params.get('currency'),
            "req_locale": post_params.get('locale'),
            "signed_date_time": post_params.get('signed_date_time'),

            # Fake data
            "req_bill_to_address_city": "Boston",
            "req_card_number": "xxxxxxxxxxxx1111",
            "req_bill_to_address_state": "MA",
            "req_bill_to_address_line1": "123 Fake Street",
            "utf8": u"✓",
            "reason_code": "100",
            "req_card_expiry_date": "01-2018",
            "req_bill_to_forename": "John",
            "req_bill_to_surname": "Doe",
            "auth_code": "888888",
            "req_bill_to_address_postal_code": "02139",
            "message": "Request was processed successfully.",
            "auth_response": "100",
            "auth_trans_ref_no": "84997128QYI23CJT",
            "auth_time": "2014-08-18T110622Z",
            "bill_trans_ref_no": "84997128QYI23CJT",
            "auth_avs_code": "X",
            "req_bill_to_email": "john@example.com",
            "auth_avs_code_raw": "I1",
            "req_profile_id": "0000001",
            "req_card_type": "001",
            "req_bill_to_address_country": "US",
            "transaction_id": "4083599817820176195662",
        }

        # Indicate which fields we are including in the signature
        # Order is important
        signed_fields = [
            'transaction_id', 'decision', 'req_access_key', 'req_profile_id',
            'req_transaction_uuid', 'req_transaction_type', 'req_reference_number',
            'req_amount', 'req_currency', 'req_locale',
            'req_payment_method', 'req_override_custom_receipt_page',
            'req_bill_to_forename', 'req_bill_to_surname',
            'req_bill_to_email', 'req_bill_to_address_line1',
            'req_bill_to_address_city', 'req_bill_to_address_state',
            'req_bill_to_address_country', 'req_bill_to_address_postal_code',
            'req_card_number', 'req_card_type', 'req_card_expiry_date',
            'message', 'reason_code', 'auth_avs_code',
            'auth_avs_code_raw', 'auth_response', 'auth_amount',
            'auth_code', 'auth_trans_ref_no', 'auth_time',
            'bill_trans_ref_no', 'signed_field_names', 'signed_date_time'
        ]

        # if decision is decline , cancel or error then remove auth_amount from signed_field.
        # list and also delete from resp_params dict

        if decision in ["DECLINE", "CANCEL", "ERROR"]:
            signed_fields.remove('auth_amount')
            del resp_params["auth_amount"]

        # Add the list of signed fields
        resp_params['signed_field_names'] = ",".join(signed_fields)

        # Calculate the public signature
        hash_val = ",".join([
            "{0}={1}".format(key, resp_params[key])
            for key in signed_fields
        ])
        resp_params['signature'] = processor_hash(hash_val)

        return resp_params

    def _payment_page_response(self, post_params):
        """
        Render the payment page to a response.  This is an HTML form
        that triggers a POST request to `callback_url`.

        The POST params are described in the CyberSource documentation:
        http://apps.cybersource.com/library/documentation/dev_guides/Secure_Acceptance_WM/Secure_Acceptance_WM.pdf

        To figure out the POST params to send to the callback,
        we either:

        1) Use fake static data (e.g. always send user name "John Doe")
        2) Use the same info we received (e.g. send the same `amount`)
        3) Dynamically calculate signatures using a shared secret
        """
        callback_url = post_params.get('override_custom_receipt_page', '/shoppingcart/postpay_callback/')

        # Build the context dict used to render the HTML form,
        # filling in values for the hidden input fields.
        # These will be sent in the POST request to the callback URL.

        post_params_success = self.response_post_params(post_params)

        # Build the context dict for decline form,
        # remove the auth_amount value from here to
        # reproduce exact response coming from actual postback call

        post_params_decline = self.response_post_params(post_params)
        del post_params_decline["auth_amount"]
        post_params_decline["decision"] = 'DECLINE'

        context_dict = {

            # URL to send the POST request to
            "callback_url": callback_url,

            # POST params embedded in the HTML success form
            'post_params_success': post_params_success,

            # POST params embedded in the HTML decline form
            'post_params_decline': post_params_decline
        }

        return render_to_response('shoppingcart/test/fake_payment_page.html', context_dict)
