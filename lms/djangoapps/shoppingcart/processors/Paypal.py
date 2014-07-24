### Implementation of support for Paypal payment processing
### The name of this file should be used as the key of the dict in the CC_PROCESSOR setting
### Implementes interface as specified by __init__.py

# TODO: Fix imports
import time
import hmac
import binascii
import re
import json
import paypalrestsdk
from paypalrestsdk import Payment
import logging
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha1
from textwrap import dedent
from django.conf import settings
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_string
from shoppingcart.models import Order
from shoppingcart.processors.exceptions import *
from microsite_configuration import microsite

# Include Headers and Content by setting logging level to DEBUG, particularly
# for Paypal-Debug-Id if requesting PayPal Merchant Tech Services for support
logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

def get_paypal_config():
    """
    This method will return any microsite specific paypal configuration,
    otherwise we return the default configuration
    """
    config_key = microsite.get_value('paypal_config_key')
    config = {}
    if config_key:
        # The microsite Paypal configuration will be subkeys inside
        # of the normal default Paypal configuration
        config = settings.CC_PROCESSOR['Paypal']['microsites'][config_key]
    else:
        config = settings.CC_PROCESSOR['Paypal']

    return config

def get_purchase_endpoint():
    return get_paypal_config().get('PURCHASE_ENDPOINT', '/shoppingcart/paypal/checkout')

def create_payment(params):
    """
    Creates the paypal payment
    """
    # TODO: Take these out and get settings using get_paypal_config
    paypalrestsdk.configure({
        "mode": "sandbox",  # sandbox or live
        "client_id": "EBWKjlELKMYqRNQ6sYvFo64FtaRLRR5BdHEESmha49TM",
        "client_secret": "EO422dn3gQLgDbuwqTjzrFgFtaRLRR5BdHEESmha49TM"
    })

    # TODO: find/make payment cancel page
    payment = paypalrestsdk.Payment({
        "intent": "sale",
        "payer": {
            "payment_method": "paypal",
        },
        "redirect_urls": {
            "return_url": "http://localhost:8000/shoppingcart/postpay_callback",
            "cancel_url": "http://localhost:8000/payment/cancel"
        },
        "transactions": [
            {
                "item_list": {
                    "items": [{
                        "name": "item",
                        "sku": str(params['orderNumber']),
                        "price": str(params['amount']),
                        "currency": str(params['currency']),
                        "quantity": 1
                    }]
                },
                "amount": {
                    "total": str(params['amount']),
                    "currency": str(params['currency'])
                },
                "description": "This is the payment transaction description."
            }]
    })

    result = payment.create()
    if result:
        print("Payment[{}] created successfully".format(payment.id))
        # return successfully created payment
        import pdb; pdb.set_trace()
        return payment
    else:
        errors = payment.errors or [""]
        print "Couldn't create payment because of error(s): {}".format(','.join(errors))
        return payment


def execute_payment(payment):
    """
    Executes payment after user vists paypal approve link
    """
    # ID of the payment. This ID is provided when creating payment.
    payment = Payment.find(payment.id)

    # PayerID is required to approve the payment.
    if payment.execute({"payer_id": payer_id}):  # return True or False
        # print("Payment {} execute successfully".format(payment.id))
        return True
    else:
        if payment.error:
            # Todo: figure out what type this (and other) exception should be
            raise Exception("Error executing payment; {}".format(payment.error))
        else:
            raise Exception("Error executing payment but paypal returned no error!")


def process_postpay_callback(params):
    """

    Verify the callback and determine if the payment was successful

    Paypal is redirected directly back to here right now. May need to make
    a view that redirects here after munging data to proper format

    The top level call to this module, basically

    It returns {'success':bool, 'order':Order, 'error_html':str}

    If successful this function must have the side effect of marking
    the order purchased and calling the purchased_callbacks of the
    cart items. If unsuccessful this function should not have those
    side effects but should try to figure out why and return a
    helpful-enough error message in error_html.
    """
    # TODO: Implement verification to confirm status of paypal purchase
    if success:
        return {'success': True, 'order': order_id, 'error_html': ""}
    else:
        return {'success': False, 'order': order_id, 'error_html': ""}
    pass


def render_purchase_form_html(cart):
    """
    Renders the HTML of the form used to initiate a Paypal purchase
    """
    return render_to_string('shoppingcart/paypal_form.html', {
        'action': get_purchase_endpoint(),
        'params': get_purchase_params(cart),
    })

def get_purchase_params(cart):
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    cart_items = cart.orderitem_set.all()
    params = OrderedDict()
    params['amount'] = amount
    params['currency'] = cart.currency
    params['orderPage_transactionType'] = 'sale'
    params['orderNumber'] = "{0:d}".format(cart.id)

    return params


def record_purchase(params, order):
    """
    Record the purchase and run purchased_callbacks
    """
    ccnum_str = params.get('card_accountNumber', '')
    m = re.search("\d", ccnum_str)
    if m:
        ccnum = ccnum_str[m.start():]
    else:
        ccnum = "####"

    order.purchase(
        first=params.get('billTo_firstName', ''),
        last=params.get('billTo_lastName', ''),
        street1=params.get('billTo_street1', ''),
        street2=params.get('billTo_street2', ''),
        city=params.get('billTo_city', ''),
        state=params.get('billTo_state', ''),
        country=params.get('billTo_country', ''),
        postalcode=params.get('billTo_postalCode', ''),
        ccnum=ccnum,
        cardtype=CARDTYPE_MAP[params.get('card_cardType', 'UNKNOWN')],
        processor_reply_dump=json.dumps(params)
    )


def get_processor_decline_html(params):
    """Have to parse through the error codes to return a helpful message"""

    # see if we have an override in the microsites
    payment_support_email = microsite.get_value('payment_support_email',
                                                settings.PAYMENT_SUPPORT_EMAIL)

    msg = dedent(_(
            """
            <p class="error_msg">
            Sorry! Our payment processor did not accept your payment.
            The decision they returned was <span class="decision">{decision}</span>,
            and the reason was <span class="reason">{reason_code}:{reason_msg}</span>.
            You were not charged. Please try a different form of payment.
            Contact us with payment-related questions at {email}.
            </p>
            """))

    return msg.format(
        decision=params['decision'],
        reason_code=params['reasonCode'],
        reason_msg=REASONCODE_MAP[params['reasonCode']],
        email=payment_support_email)


def get_processor_exception_html(exception):
    """Return error HTML associated with exception"""

    # see if we have an override in the microsites
    payment_support_email = microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)
    if isinstance(exception, CCProcessorDataException):
        msg = dedent(_(
                """
                <p class="error_msg">
                Sorry! Our payment processor sent us back a payment confirmation that had inconsistent data!
                We apologize that we cannot verify whether the charge went through and take further action on your order.
                The specific error message is: <span class="exception_msg">{msg}</span>.
                Your credit card may possibly have been charged.  Contact us with payment-specific questions at {email}.
                </p>
                """.format(msg=exception.message, email=payment_support_email)))
        return msg
    elif isinstance(exception, CCProcessorWrongAmountException):
        msg = dedent(_(
                """
                <p class="error_msg">
                Sorry! Due to an error your purchase was charged for a different amount than the order total!
                The specific error message is: <span class="exception_msg">{msg}</span>.
                Your credit card has probably been charged. Contact us with payment-specific questions at {email}.
                </p>
                """.format(msg=exception.message, email=payment_support_email)))
        return msg
    elif isinstance(exception, CCProcessorSignatureException):
        msg = dedent(_(
                """
                <p class="error_msg">
                Sorry! Our payment processor sent us back a corrupted message regarding your charge, so we are
                unable to validate that the message actually came from the payment processor.
                The specific error message is: <span class="exception_msg">{msg}</span>.
                We apologize that we cannot verify whether the charge went through and take further action on your order.
                Your credit card may possibly have been charged.  Contact us with payment-specific questions at {email}.
                </p>
                """.format(msg=exception.message, email=payment_support_email)))
        return msg

    # fallthrough case, which basically never happens
    return '<p class="error_msg">EXCEPTION!</p>'


# CARDTYPE_MAP = defaultdict(lambda: "UNKNOWN")
# CARDTYPE_MAP.update(
#     {
#         '001': 'Visa',
#         '002': 'MasterCard',
#         '003': 'American Express',
#         '004': 'Discover',
#         '005': 'Diners Club',
#         '006': 'Carte Blanche',
#         '007': 'JCB',
#         '014': 'EnRoute',
#         '021': 'JAL',
#         '024': 'Maestro',
#         '031': 'Delta',
#         '033': 'Visa Electron',
#         '034': 'Dankort',
#         '035': 'Laser',
#         '036': 'Carte Bleue',
#         '037': 'Carta Si',
#         '042': 'Maestro',
#         '043': 'GE Money UK card'
#     }
# )
