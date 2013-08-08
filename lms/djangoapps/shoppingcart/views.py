import logging
import random
import time
import hmac
import binascii
from hashlib import sha1

from django.conf import settings
from collections import OrderedDict
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response
from .inventory_types import *

log = logging.getLogger("shoppingcart")


def test(request, course_id):
    item1 = PaidCourseRegistration(course_id, 200)
    item1.purchased_callback(request.user.id)
    return HttpResponse('OK')

@login_required
def add_course_to_cart(request, course_id):
    cart = request.session.get('shopping_cart', [])
    course_ids_in_cart = [i.course_id for i in cart if isinstance(i, PaidCourseRegistration)]
    if course_id not in course_ids_in_cart:
        # TODO: Catch 500 here for course that does not exist, period
        item = PaidCourseRegistration(course_id, 200)
        cart.append(item)
        request.session['shopping_cart'] = cart
        return HttpResponse('Added')
    else:
        return HttpResponse("Item exists, not adding")

@login_required
def show_cart(request):
    cart = request.session.get('shopping_cart', [])
    total_cost = "{0:0.2f}".format(sum([i.line_cost for i in cart]))
    params = OrderedDict()
    params['amount'] = total_cost
    params['currency'] = 'usd'
    params['orderPage_transactionType'] = 'sale'
    params['orderNumber'] = "{0:d}".format(random.randint(1, 10000))
    signed_param_dict = cybersource_sign(params)
    return render_to_response("shoppingcart/list.html",
                              {'shoppingcart_items': cart,
                               'total_cost': total_cost,
                               'params': signed_param_dict,
                               })

@login_required
def clear_cart(request):
    request.session['shopping_cart'] = []
    return HttpResponse('Cleared')

@login_required
def remove_item(request):
    # doing this with indexes to replicate the function that generated the list on the HTML page
    item_idx = request.REQUEST.get('idx', 'blank')
    try:
        cart = request.session.get('shopping_cart', [])
        cart.pop(int(item_idx))
        request.session['shopping_cart'] = cart
    except IndexError, ValueError:
        log.exception('Cannot remove element at index {0} from cart'.format(item_idx))
    return HttpResponse('OK')


def cybersource_sign(params):
    """
    params needs to be an ordered dict, b/c cybersource documentation states that order is important.
    Reverse engineered from PHP version provided by cybersource
    """
    shared_secret = settings.CYBERSOURCE.get('SHARED_SECRET','')
    merchant_id =  settings.CYBERSOURCE.get('MERCHANT_ID','')
    serial_number = settings.CYBERSOURCE.get('SERIAL_NUMBER','')
    orderPage_version = settings.CYBERSOURCE.get('ORDERPAGE_VERSION','7')
    params['merchantID'] = merchant_id
    params['orderPage_timestamp'] = int(time.time()*1000)
    params['orderPage_version'] = orderPage_version
    params['orderPage_serialNumber'] = serial_number
    fields = ",".join(params.keys())
    values = ",".join(["{0}={1}".format(i,params[i]) for i in params.keys()])
    fields_hash_obj = hmac.new(shared_secret, fields, sha1)
    fields_sig = binascii.b2a_base64(fields_hash_obj.digest())[:-1] # last character is a '\n', which we don't want
    values += ",signedFieldsPublicSignature=" + fields_sig
    values_hash_obj = hmac.new(shared_secret, values, sha1)
    params['orderPage_signaturePublic'] = binascii.b2a_base64(values_hash_obj.digest())[:-1]
    params['orderPage_signedFields'] = fields

    return params