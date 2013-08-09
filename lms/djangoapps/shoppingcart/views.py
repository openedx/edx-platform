import logging
import random
import time
import hmac
import binascii
from hashlib import sha1

from django.conf import settings
from collections import OrderedDict
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from mitxmako.shortcuts import render_to_response
from .models import *

log = logging.getLogger("shoppingcart")


def test(request, course_id):
    item1 = PaidCourseRegistration(course_id, 200)
    item1.purchased_callback(request.user.id)
    return HttpResponse('OK')

@login_required
def purchased(request):
    #verify() -- signatures, total cost match up, etc.  Need error handling code (
    # If verify fails probaly need to display a contact email/number)
    cart = Order.get_cart_for_user(request.user)
    cart.purchase()
    return HttpResponseRedirect('/')

@login_required
def add_course_to_cart(request, course_id):
    cart = Order.get_cart_for_user(request.user)
    # TODO: Catch 500 here for course that does not exist, period
    PaidCourseRegistration.add_to_order(cart, course_id, 200)
    return HttpResponse("Added")

@login_required
def show_cart(request):
    cart = Order.get_cart_for_user(request.user)
    total_cost = cart.total_cost
    cart_items = cart.orderitem_set.all()
    params = OrderedDict()
    params['amount'] = total_cost
    params['currency'] = 'usd'
    params['orderPage_transactionType'] = 'sale'
    params['orderNumber'] = "{0:d}".format(cart.id)
    params['billTo_email'] = request.user.email
    idx=1
    for item in cart_items:
        prefix = "item_{0:d}_".format(idx)
        params[prefix+'productSKU'] = "{0:d}".format(item.id)
        params[prefix+'quantity'] = item.qty
        params[prefix+'productName'] = item.line_desc
        params[prefix+'unitPrice'] = item.unit_cost
        params[prefix+'taxAmount'] = "0.00"
    signed_param_dict = cybersource_sign(params)
    return render_to_response("shoppingcart/list.html",
                              {'shoppingcart_items': cart_items,
                               'total_cost': total_cost,
                               'params': signed_param_dict,
                               })

@login_required
def clear_cart(request):
    cart = Order.get_cart_for_user(request.user)
    cart.orderitem_set.all().delete()
    return HttpResponse('Cleared')

@login_required
def remove_item(request):
    item_id = request.REQUEST.get('id', '-1')
    try:
        item = OrderItem.objects.get(id=item_id, status='cart')
        if item.user == request.user:
            item.delete()
    except OrderItem.DoesNotExist:
        log.exception('Cannot remove cart OrderItem id={0}. DoesNotExist or item is already purchased'.format(item_id))
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