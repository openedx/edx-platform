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
from shoppingcart.processors.CyberSource import processor_hash


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
            - Most of this data is duplicated from the request POST params (e.g. `amount` and `course_id`)
            - Other params contain fake data (always the same user name and address.
            - Still other params are calculated (signatures)

        * Serves an error page (HTML) with a 200 status code
          if the signatures are invalid.  This is what CyberSource does.

        Since all the POST requests are triggered by HTML forms, this is
        equivalent to the CyberSource payment page, even though it's
        served by the shopping cart app.
        """
        if self._is_signature_valid(request.POST):
            return self._payment_page_response(request.POST, '/shoppingcart/postpay_callback/')

        else:
            return render_to_response('shoppingcart/test/fake_payment_error.html')

    def put(self, request):
        """
        Set the status of payment requests to success or failure.

        Accepts one POST param "status" that can be either "success"
        or "failure".
        """
        new_status = request.body

        if not new_status in ["success", "failure"]:
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

        # Calculate the fields signature
        fields_sig = processor_hash(post_params.get('orderPage_signedFields'))

        # Retrieve the list of signed fields
        signed_fields = post_params.get('orderPage_signedFields').split(',')

        # Calculate the public signature
        hash_val = ",".join([
            "{0}={1}".format(key, post_params[key])
            for key in signed_fields
        ]) + ",signedFieldsPublicSignature={0}".format(fields_sig)

        public_sig = processor_hash(hash_val)

        return public_sig == post_params.get('orderPage_signaturePublic')

    @classmethod
    def response_post_params(cls, post_params):
        """
        Calculate the POST params we want to send back to the client.
        """
        resp_params = {
            # Indicate whether the payment was successful
            "decision": "ACCEPT" if cls.PAYMENT_STATUS_RESPONSE == "success" else "REJECT",

            # Reflect back whatever the client sent us,
            # defaulting to `None` if a paramter wasn't received
            "course_id": post_params.get('course_id'),
            "orderAmount": post_params.get('amount'),
            "ccAuthReply_amount": post_params.get('amount'),
            "orderPage_transactionType": post_params.get('orderPage_transactionType'),
            "orderPage_serialNumber": post_params.get('orderPage_serialNumber'),
            "orderNumber": post_params.get('orderNumber'),
            "orderCurrency": post_params.get('currency'),
            "match": post_params.get('match'),
            "merchantID": post_params.get('merchantID'),

            # Send fake user data
            "billTo_firstName": "John",
            "billTo_lastName": "Doe",
            "billTo_street1": "123 Fake Street",
            "billTo_state": "MA",
            "billTo_city": "Boston",
            "billTo_postalCode": "02134",
            "billTo_country": "us",

            # Send fake data for other fields
            "card_cardType": "001",
            "card_accountNumber": "############1111",
            "card_expirationMonth": "08",
            "card_expirationYear": "2019",
            "paymentOption": "card",
            "orderPage_environment": "TEST",
            "orderPage_requestToken": "unused",
            "reconciliationID": "39093601YKVO1I5D",
            "ccAuthReply_authorizationCode": "888888",
            "ccAuthReply_avsCodeRaw": "I1",
            "reasonCode": "100",
            "requestID": "3777139938170178147615",
            "ccAuthReply_reasonCode": "100",
            "ccAuthReply_authorizedDateTime": "2013-08-28T181954Z",
            "ccAuthReply_processorResponse": "100",
            "ccAuthReply_avsCode": "X",

            # We don't use these signatures
            "transactionSignature": "unused=",
            "decision_publicSignature": "unused=",
            "orderAmount_publicSignature": "unused=",
            "orderNumber_publicSignature": "unused=",
            "orderCurrency_publicSignature": "unused=",
        }

        # Indicate which fields we are including in the signature
        # Order is important
        signed_fields = [
            'billTo_lastName', 'orderAmount', 'course_id',
            'billTo_street1', 'card_accountNumber', 'orderAmount_publicSignature',
            'orderPage_serialNumber', 'orderCurrency', 'reconciliationID',
            'decision', 'ccAuthReply_processorResponse', 'billTo_state',
            'billTo_firstName', 'card_expirationYear', 'billTo_city',
            'billTo_postalCode', 'orderPage_requestToken', 'ccAuthReply_amount',
            'orderCurrency_publicSignature', 'orderPage_transactionType',
            'ccAuthReply_authorizationCode', 'decision_publicSignature',
            'match', 'ccAuthReply_avsCodeRaw', 'paymentOption',
            'billTo_country', 'reasonCode', 'ccAuthReply_reasonCode',
            'orderPage_environment', 'card_expirationMonth', 'merchantID',
            'orderNumber_publicSignature', 'requestID', 'orderNumber',
            'ccAuthReply_authorizedDateTime', 'card_cardType', 'ccAuthReply_avsCode'
        ]

        # Add the list of signed fields
        resp_params['signedFields'] = ",".join(signed_fields)

        # Calculate the fields signature
        signed_fields_sig = processor_hash(resp_params['signedFields'])

        # Calculate the public signature
        hash_val = ",".join([
            "{0}={1}".format(key, resp_params[key])
            for key in signed_fields
        ]) + ",signedFieldsPublicSignature={0}".format(signed_fields_sig)

        resp_params['signedDataPublicSignature'] = processor_hash(hash_val)

        return resp_params

    def _payment_page_response(self, post_params, callback_url):
        """
        Render the payment page to a response.  This is an HTML form
        that triggers a POST request to `callback_url`.

        The POST params are described in the CyberSource documentation:
        http://apps.cybersource.com/library/documentation/dev_guides/HOP_UG/html/wwhelp/wwhimpl/js/html/wwhelp.htm

        To figure out the POST params to send to the callback,
        we either:

        1) Use fake static data (e.g. always send user name "John Doe")
        2) Use the same info we received (e.g. send the same `course_id` and `amount`)
        3) Dynamically calculate signatures using a shared secret
        """

        # Build the context dict used to render the HTML form,
        # filling in values for the hidden input fields.
        # These will be sent in the POST request to the callback URL.
        context_dict = {

            # URL to send the POST request to
            "callback_url": callback_url,

            # POST params embedded in the HTML form
            'post_params': self.response_post_params(post_params)
        }

        return render_to_response('shoppingcart/test/fake_payment_page.html', context_dict)
