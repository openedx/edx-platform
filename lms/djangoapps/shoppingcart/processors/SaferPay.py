### Implementation of support for the SaferPay Credit card processor
### The name of this file should be used as the key of the dict in the CC_PROCESSOR setting
### Implementes interface as specified by __init__.py

import requests
import logging
import urlparse
import json

from django.conf import settings
from django.utils.translation import ugettext as _
from edxmako.shortcuts import render_to_string
from shoppingcart.models import Order
from shoppingcart.processors.exceptions import *

from django.core.urlresolvers import reverse

logger = logging.getLogger('shoppingcart.processors.saferpay')

def render_purchase_form_html(cart):
    """
    Renders the HTML of the hidden POST form that must be used to initiate a purchase with CyberSource
    """
    return render_to_string('shoppingcart/saferpay_form.html', {
        'action': reverse('shoppingcart.views.purchase_callback'),
        'params': {
            'order_id': cart.id,
        },
    })


def process_purchase_callback(params):
    """
    This is the implemention of this interface point.
    Here we prepare to redirect the user to SaferPay website to complete the purchase
    transaction
    """
    order_id = params['order_id']
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("Could not find a corresponding order number."))

    description = ''
    for item in order.orderitem_set.all():
        description += item.line_desc + '\n'

    callback_url_domain = 'http://localhost:8000'
    data = {
        'AMOUNT': int(order.total_cost * 100),
        'CURRENCY': 'USD',
        'DESCRIPTION': description,
        'LANGID': 'en',
        'ALLOWCOLLECT': 'no',
        'DELIVERY': 'no',
        'ACCOUNTID': settings.CC_PROCESSOR['SaferPay'].get('ACCOUNTID', ''),
        'ORDERID': settings.CC_PROCESSOR['SaferPay'].get('ORDERID_PREFIX', '') + str(order_id),
        'SUCCESSLINK': callback_url_domain + reverse('shoppingcart.views.postpay_callback') + '?order_id={0}'.format(order_id),
        'BACKLINK': callback_url_domain + reverse('shoppingcart.views.postpay_callback'),
        'FAILLINK': callback_url_domain + reverse('shoppingcart.views.postpay_callback'),
    }

    for style in ('BODYCOLOR', 'HEADCOLOR', 'HEADLINECOLOR', 'MENUCOLOR', 'BODYFONTCOLOR', 'HEADFONTCOLOR', 'MENUFONTCOLOR', 'FONT'):
        style_value = settings.CC_PROCESSOR['SaferPay'].get(style)
        if style_value is not None:
            data[style] = style_value

    response = requests.get(settings.CC_PROCESSOR['SaferPay'].get('PROCESS_URL',''), params=data)
    logger.info('Saferpay: order {0} redirected to saferpay gateway'.format(order_id))
    return {
        'redirect_url': response.content,
        'success': True,
    }


def process_postpay_callback(params):
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

    order_id = params['order_id']

    order_id = params['order_id']
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("Could not find a corresponding order number."))

    data = {
        'SIGNATURE': params['SIGNATURE'],
        'DATA': params['DATA'],
    }

    logger.info('Saferpay: order {0} verifying , DATA: {1}, SIGNATURE {2}'.format(order.pk, data['DATA'], data['SIGNATURE']))

    response = requests.get(settings.CC_PROCESSOR['SaferPay'].get('VERIFY_URL'), params=data)

    result = {
        'order': order,
    }
    if response.status_code == 200 and response.content.startswith('OK'):
        response_data = urlparse.parse_qs(response.content[3:])
        order.purchase(
            processor_reply_dump=json.dumps(response_data)
        )
        result['success'] = True
    else:
        result['success'] = False

    return result

