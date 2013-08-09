### Implementation of support for the Cybersource Credit card processor
### The name of this file should be used as the key of the dict in the CC_PROCESSOR setting

import time
import hmac
import binascii
from collections import OrderedDict
from hashlib import sha1
from django.conf import settings
from mitxmako.shortcuts import render_to_string

shared_secret = settings.CC_PROCESSOR['CyberSource'].get('SHARED_SECRET','')
merchant_id = settings.CC_PROCESSOR['CyberSource'].get('MERCHANT_ID','')
serial_number = settings.CC_PROCESSOR['CyberSource'].get('SERIAL_NUMBER','')
orderPage_version = settings.CC_PROCESSOR['CyberSource'].get('ORDERPAGE_VERSION','7')
purchase_endpoint = settings.CC_PROCESSOR['CyberSource'].get('PURCHASE_ENDPOINT','')

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

def verify(params):
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
    total_cost = cart.total_cost
    amount = "{0:0.2f}".format(total_cost)
    cart_items = cart.orderitem_set.all()
    params = OrderedDict()
    params['comment'] = 'Stanford OpenEdX Purchase'
    params['amount'] = amount
    params['currency'] = cart.currency
    params['orderPage_transactionType'] = 'sale'
    params['orderNumber'] = "{0:d}".format(cart.id)
    params['billTo_email'] = user.email
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