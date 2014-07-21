### Implementation of support for the Cybersource Credit card processor using the new
### Secure Acceptance API. The previous Hosted Order Page API is being deprecated as of 9/14
### It is mostly the same as the CyberSource.py file, but we have a new file so that we can
### maintain some backwards-compatibility in case of a need to quickly roll back (i.e.
### configuration change rather than code rollback )

### The name of this file should be used as the key of the dict in the CC_PROCESSOR setting
### Implementes interface as specified by __init__.py

import hmac
import binascii
import re
import json
import uuid
from datetime import datetime
from collections import OrderedDict, defaultdict
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from textwrap import dedent
from django.conf import settings
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_string
from shoppingcart.models import Order
from shoppingcart.processors.exceptions import *
from microsite_configuration import microsite
from django.core.urlresolvers import reverse


def get_cybersource_config():
    """
    This method will return any microsite specific cybersource configuration, otherwise
    we return the default configuration
    """
    config_key = microsite.get_value('cybersource_config_key')
    config = {}
    if config_key:
        # The microsite CyberSource configuration will be subkeys inside of the normal default
        # CyberSource configuration
        config = settings.CC_PROCESSOR['CyberSource2']['microsites'][config_key]
    else:
        config = settings.CC_PROCESSOR['CyberSource2']

    return config


def process_postpay_callback(params):
    """
    The top level call to this module, basically
    This function is handed the callback request after the customer has entered the CC info and clicked "buy"
    on the external Hosted Order Page.
    It is expected to verify the callback and determine if the payment was successful.
    It returns {'success':bool, 'order':Order, 'error_html':str}
    If successful this function must have the side effect of marking the order purchased and calling the
    purchased_callbacks of the cart  items.
    If unsuccessful this function should not have those side effects but should try to figure out why and
    return a helpful-enough error message in error_html.
    """
    try:
        result = payment_accepted(params)
        if result['accepted']:
            # SUCCESS CASE first, rest are some sort of oddity
            record_purchase(params, result['order'])
            return {'success': True,
                    'order': result['order'],
                    'error_html': ''}
        else:
            return {'success': False,
                    'order': result['order'],
                    'error_html': get_processor_decline_html(params)}
    except CCProcessorException as error:
        return {'success': False,
                'order': None,  # due to exception we may not have the order
                'error_html': get_processor_exception_html(error)}


def processor_hash(value):
    """
    Performs the base64(HMAC_SHA1(key, value)) used by CyberSource Hosted Order Page
    """
    secret_key = get_cybersource_config().get('SECRET_KEY', '')
    hash_obj = hmac.new(secret_key, value, sha256)
    return binascii.b2a_base64(hash_obj.digest())[:-1]  # last character is a '\n', which we don't want


def sign(params, signed_fields_key='signed_field_names', full_sig_key='signature'):
    """
    params needs to be an ordered dict, b/c cybersource documentation states that order is important.
    Reverse engineered from PHP version provided by cybersource
    """
    fields = u",".join(params.keys())
    params[signed_fields_key] = fields

    signed_fields = params.get(signed_fields_key, '').split(',')
    values = u",".join([u"{0}={1}".format(i, params.get(i, '')) for i in signed_fields])
    params[full_sig_key] = processor_hash(values)
    params[signed_fields_key] = fields

    return params


def render_purchase_form_html(cart):
    """
    Renders the HTML of the hidden POST form that must be used to initiate a purchase with CyberSource
    """
    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': get_purchase_endpoint(),
        'params': get_signed_purchase_params(cart),
    })


def get_signed_purchase_params(cart):
    """
    This method will return a digitally signed set of CyberSource parameters
    """
    return sign(get_purchase_params(cart))


def get_purchase_params(cart):
    """
    This method will build out a dictionary of parameters needed by CyberSource to complete the transaction
    """
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    params = OrderedDict()

    params['amount'] = amount
    params['currency'] = cart.currency
    params['orderNumber'] = "OrderId: {0:d}".format(cart.id)

    params['access_key'] = get_cybersource_config().get('ACCESS_KEY', '')
    params['profile_id'] = get_cybersource_config().get('PROFILE_ID', '')
    params['reference_number'] = cart.id
    params['transaction_type'] = 'sale'

    params['locale'] = 'en'
    params['signed_date_time'] =  datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    params['signed_field_names'] = 'access_key,profile_id,amount,currency,transaction_type,reference_number,signed_date_time,locale,transaction_uuid,signed_field_names,unsigned_field_names,orderNumber'
    params['unsigned_field_names'] = ''
    params['transaction_uuid'] = uuid.uuid4()
    params['payment_method'] = 'card'

    if hasattr(cart, 'context') and 'request_domain' in cart.context:
        params['override_custom_receipt_page'] = '{0}{1}'.format(
            cart.context['request_domain'],
            reverse('shoppingcart.views.postpay_callback')
        )

    return params


def get_purchase_endpoint():
    """
    Helper function to return the CyberSource endpoint configuration
    """
    return get_cybersource_config().get('PURCHASE_ENDPOINT', '')


def payment_accepted(params):
    """
    Check that cybersource has accepted the payment
    params: a dictionary of POST parameters returned by CyberSource in their post-payment callback

    returns: true if the payment was correctly accepted, for the right amount
             false if the payment was not accepted

    raises: CCProcessorDataException if the returned message did not provide required parameters
            CCProcessorWrongAmountException if the amount charged is different than the order amount

    """
    #make sure required keys are present and convert their values to the right type
    valid_params = {}
    for key, key_type in [('req_reference_number', int),
                          ('req_currency', str),
                          ('decision', str)]:
        if key not in params:
            raise CCProcessorDataException(
                _("The payment processor did not return a required parameter: {0}".format(key))
            )
        try:
            valid_params[key] = key_type(params[key])
        except ValueError:
            raise CCProcessorDataException(
                _("The payment processor returned a badly-typed value {0} for param {1}.".format(params[key], key))
            )

    try:
        order = Order.objects.get(id=valid_params['req_reference_number'])
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("The payment processor accepted an order whose number is not in our system."))

    if valid_params['decision'] == 'ACCEPT':
        try:
            # Moved reading of charged_amount here from the valid_params loop above because
            # only 'ACCEPT' messages have a 'ccAuthReply_amount' parameter
            charged_amt = Decimal(params['auth_amount'])
        except InvalidOperation:
            raise CCProcessorDataException(
                _("The payment processor returned a badly-typed value {0} for param {1}.".format(
                    params['auth_amount'], 'auth_amount'))
            )

        if charged_amt == order.total_cost and valid_params['req_currency'] == order.currency:
            return {'accepted': True,
                    'amt_charged': charged_amt,
                    'currency': valid_params['req_currency'],
                    'order': order}
        else:
            raise CCProcessorWrongAmountException(
                _("The amount charged by the processor {0} {1} is different than the total cost of the order {2} {3}."
                    .format(charged_amt, valid_params['req_currency'],
                            order.total_cost, order.currency))
            )
    else:
        return {'accepted': False,
                'amt_charged': 0,
                'currency': 'usd',
                'order': order}


def record_purchase(params, order):
    """
    Record the purchase and run purchased_callbacks
    """
    ccnum_str = params.get('req_card_number', '')
    mm = re.search("\d", ccnum_str)
    if mm:
        ccnum = ccnum_str[mm.start():]
    else:
        ccnum = "####"

    order.purchase(
        first=params.get('req_bill_to_forename', ''),
        last=params.get('req_bill_to_surname', ''),
        street1=params.get('req_bill_to_address_line1', ''),
        street2=params.get('req_bill_to_address_line2', ''),
        city=params.get('req_bill_to_address_city', ''),
        state=params.get('req_bill_to_address_state', ''),
        country=params.get('req_bill_to_address_country', ''),
        postalcode=params.get('req_bill_to_address_postal_code', ''),
        ccnum=ccnum,
        cardtype=CARDTYPE_MAP[params.get('req_card_type', '')],
        processor_reply_dump=json.dumps(params)
    )


def get_processor_decline_html(params):
    """Have to parse through the error codes to return a helpful message"""
    payment_support_email = microsite.get_value('payment_support_email', settings.PAYMENT_SUPPORT_EMAIL)

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
        reason_code=params['reason_code'],
        reason_msg=REASONCODE_MAP[params['reason_code']],
        email=payment_support_email
    )


def get_processor_exception_html(exception):
    """Return error HTML associated with exception"""

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

    # fallthrough case, which basically never happens
    return '<p class="error_msg">EXCEPTION!</p>'


CARDTYPE_MAP = defaultdict(lambda: "UNKNOWN")
CARDTYPE_MAP.update(
    {
        '001': 'Visa',
        '002': 'MasterCard',
        '003': 'American Express',
        '004': 'Discover',
        '005': 'Diners Club',
        '006': 'Carte Blanche',
        '007': 'JCB',
        '014': 'EnRoute',
        '021': 'JAL',
        '024': 'Maestro',
        '031': 'Delta',
        '033': 'Visa Electron',
        '034': 'Dankort',
        '035': 'Laser',
        '036': 'Carte Bleue',
        '037': 'Carta Si',
        '042': 'Maestro Int.',
        '043': 'GE Money UK card'
    }
)

REASONCODE_MAP = defaultdict(lambda: "UNKNOWN REASON")
REASONCODE_MAP.update(
    {
        '100': _('Successful transaction.'),
        '102': _('One or more fields in the request contains invalid data.'),
        '104': dedent(_(
            """
            The access_key and transaction_uuid fields for this authorization request matches the access_key and
            transaction_uuid of another authorization request that you sent in the last 15 minutes.
            Possible fix: retry the payment after 15 minutes.
            """)),
        '110': _('Only a partial amount was approved.'),
        '200': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource
            because it did not pass the Address Verification System (AVS).
            """)),
        '201': dedent(_(
            """
            The issuing bank has questions about the request. You do not receive an
            authorization code programmatically, but you might receive one verbally by calling the processor.
            Possible fix: retry with another form of payment
            """)),
        '202': dedent(_(
            """
            Expired card. You might also receive this if the expiration date you
            provided does not match the date the issuing bank has on file.
            Possible fix: retry with another form of payment
            """)),
        '203': dedent(_(
            """
            General decline of the card. No other information provided by the issuing bank.
            Possible fix: retry with another form of payment
            """)),
        '204': _('Insufficient funds in the account. Possible fix: retry with another form of payment'),
        # 205 was Stolen or lost card.  Might as well not show this message to the person using such a card.
        '205': _('Stolen or lost card'),
        '207': _('Issuing bank unavailable. Possible fix: retry again after a few minutes'),
        '208': dedent(_(
            """
            Inactive card or card not authorized for card-not-present transactions.
            Possible fix: retry with another form of payment
            """)),
        '210': _('The card has reached the credit limit. Possible fix: retry with another form of payment'),
        '211': _('Invalid card verification number (CVN). Possible fix: retry with another form of payment'),
        # 221 was The customer matched an entry on the processor's negative file.
        # Might as well not show this message to the person using such a card.
        '221': _('The customer matched an entry on the processors negative file.'),
        '222': _('Account frozen. Possible fix: retry with another form of payment'),
        '230': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by
            CyberSource because it did not pass the CVN check.
            Possible fix: retry with another form of payment
            """)),
        '231': _('Invalid account number. Possible fix: retry with another form of payment'),
        '232': dedent(_(
            """
            The card type is not accepted by the payment processor.
            Possible fix: retry with another form of payment
            """)),
        '233': _('General decline by the processor.  Possible fix: retry with another form of payment'),
        '234': dedent(_(
            """
            There is a problem with the information in your CyberSource account.  Please let us know at {0}
            """.format(settings.PAYMENT_SUPPORT_EMAIL))),
        '236': _('Processor Failure.  Possible fix: retry the payment'),
        '240': dedent(_(
            """
            The card type sent is invalid or does not correlate with the credit card number.
            Possible fix: retry with the same card or another form of payment
            """)),
        '475': _('The cardholder is enrolled for payer authentication'),
        '476': _('Payer authentication could not be authenticated'),
        '520': dedent(_(
            """
            The authorization request was approved by the issuing bank but declined by CyberSource based
            on your legacy Smart Authorization settings.
            Possible fix: retry with a different form of payment.
            """)),
    }
)
