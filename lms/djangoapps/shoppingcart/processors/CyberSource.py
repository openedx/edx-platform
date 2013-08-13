### Implementation of support for the Cybersource Credit card processor
### The name of this file should be used as the key of the dict in the CC_PROCESSOR setting
### Implementes interface as specified by __init__.py

import time
import hmac
import binascii
import re
import json
from collections import OrderedDict, defaultdict
from hashlib import sha1
from django.conf import settings
from django.utils.translation import ugettext as _
from mitxmako.shortcuts import render_to_string
from shoppingcart.models import Order
from .exceptions import CCProcessorException, CCProcessorDataException, CCProcessorWrongAmountException

shared_secret = settings.CC_PROCESSOR['CyberSource'].get('SHARED_SECRET','')
merchant_id = settings.CC_PROCESSOR['CyberSource'].get('MERCHANT_ID','')
serial_number = settings.CC_PROCESSOR['CyberSource'].get('SERIAL_NUMBER','')
orderPage_version = settings.CC_PROCESSOR['CyberSource'].get('ORDERPAGE_VERSION','7')
purchase_endpoint = settings.CC_PROCESSOR['CyberSource'].get('PURCHASE_ENDPOINT','')

def process_postpay_callback(request):
    """
    The top level call to this module, basically
    This function is handed the callback request after the customer has entered the CC info and clicked "buy"
    on the external Hosted Order Page.
    It is expected to verify the callback and determine if the payment was successful.
    It returns {'success':bool, 'order':Order, 'error_html':str}
    If successful this function must have the side effect of marking the order purchased and calling the
    purchased_callbacks of the cart items.
    If unsuccessful this function should not have those side effects but should try to figure out why and
    return a helpful-enough error message in error_html.
    """
    params = request.POST.dict()
    if verify_signatures(params):
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
                        'error_html': get_processor_error_html(params)}
        except CCProcessorException as e:
            return {'success': False,
                    'order': None, #due to exception we may not have the order
                    'error_html': get_exception_html(params, e)}
    else:
        return {'success': False,
                'order': None,
                'error_html': get_signature_error_html(params)}


def hash(value):
    """
    Performs the base64(HMAC_SHA1(key, value)) used by CyberSource Hosted Order Page
    """
    hash_obj = hmac.new(shared_secret, value, sha1)
    return binascii.b2a_base64(hash_obj.digest())[:-1] # last character is a '\n', which we don't want


def sign(params):
    """
    params needs to be an ordered dict, b/c cybersource documentation states that order is important.
    Reverse engineered from PHP version provided by cybersource
    """
    params['merchantID'] = merchant_id
    params['orderPage_timestamp'] = int(time.time()*1000)
    params['orderPage_version'] = orderPage_version
    params['orderPage_serialNumber'] = serial_number
    fields = ",".join(params.keys())
    values = ",".join(["{0}={1}".format(i,params[i]) for i in params.keys()])
    fields_sig = hash(fields)
    values += ",signedFieldsPublicSignature=" + fields_sig
    params['orderPage_signaturePublic'] = hash(values)
    params['orderPage_signedFields'] = fields

    return params


def verify_signatures(params):
    """
    Verify the signatures accompanying the POST back from Cybersource Hosted Order Page
    """
    signed_fields = params.get('signedFields', '').split(',')
    data = ",".join(["{0}={1}".format(k, params.get(k, '')) for k in signed_fields])
    signed_fields_sig = hash(params.get('signedFields', ''))
    data += ",signedFieldsPublicSignature=" + signed_fields_sig
    returned_sig = params.get('signedDataPublicSignature','')
    if not returned_sig:
        return False
    return hash(data) == returned_sig


def render_purchase_form_html(cart, user):
    """
    Renders the HTML of the hidden POST form that must be used to initiate a purchase with CyberSource
    """
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    cart_items = cart.orderitem_set.all()
    params = OrderedDict()
    params['comment'] = 'Stanford OpenEdX Purchase'
    params['amount'] = amount
    params['currency'] = cart.currency
    params['orderPage_transactionType'] = 'sale'
    params['orderNumber'] = "{0:d}".format(cart.id)
    idx=1
    for item in cart_items:
        prefix = "item_{0:d}_".format(idx)
        params[prefix+'productSKU'] = "{0:d}".format(item.id)
        params[prefix+'quantity'] = item.qty
        params[prefix+'productName'] = item.line_desc
        params[prefix+'unitPrice'] = item.unit_cost
        params[prefix+'taxAmount'] = "0.00"
    signed_param_dict = sign(params)

    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': purchase_endpoint,
        'params': signed_param_dict,
    })


def payment_accepted(params):
    """
    Check that cybersource has accepted the payment
    """
    #make sure required keys are present and convert their values to the right type
    valid_params = {}
    for key, type in [('orderNumber', int),
                      ('ccAuthReply_amount', float),
                      ('orderCurrency', str),
                      ('decision', str)]:
        if key not in params:
            raise CCProcessorDataException(
                _("The payment processor did not return a required parameter: {0}".format(key))
            )
        try:
            valid_params[key] = type(params[key])
        except ValueError:
            raise CCProcessorDataException(
                _("The payment processor returned a badly-typed value {0} for param {1}.".format(params[key], key))
            )

    try:
        order = Order.objects.get(id=valid_params['orderNumber'])
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("The payment processor accepted an order whose number is not in our system."))

    if valid_params['decision'] == 'ACCEPT':
        if valid_params['ccAuthReply_amount'] == order.total_cost and valid_params['orderCurrency'] == order.currency:
            return {'accepted': True,
                    'amt_charged': valid_params['ccAuthReply_amount'],
                    'currency': valid_params['orderCurrency'],
                    'order': order}
        else:
            raise CCProcessorWrongAmountException(
                _("The amount charged by the processor {0} {1} is different than the total cost of the order {2} {3}."\
                    .format(valid_params['ccAuthReply_amount'], valid_params['orderCurrency'],
                            order.total_cost, order.currency))
            )
    else:
        return {'accepted': False,
                'amt_charged': 0,
                'currency': 'usd',
                'order': None}


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
        postalcode=params.get('billTo_postalCode',''),
        ccnum=ccnum,
        cardtype=CARDTYPE_MAP[params.get('card_cardType', 'UNKNOWN')],
        processor_reply_dump=json.dumps(params)
    )

def get_processor_error_html(params):
    """Have to parse through the error codes for all the other cases"""
    return "<p>ERROR!</p>"

def get_exception_html(params, exp):
    """Return error HTML associated with exception"""
    return "<p>EXCEPTION!</p>"

def get_signature_error_html(params):
    """Return error HTML associated with signature failure"""
    return "<p>EXCEPTION!</p>"


CARDTYPE_MAP = defaultdict(lambda:"UNKNOWN")
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
        '042': 'Maestro',
        '043': 'GE Money UK card'
    }
)
