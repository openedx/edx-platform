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
    Renders the HTML of the hidden POST. In the SaferPay case, we want to post back to ourselves and then
    we will turn around and setup the redirect to the SaferPay website
    """
    return render_to_string('shoppingcart/saferpay_form.html', {
        'action': reverse('shoppingcart.views.start_payment'),
        'params': {
            'order_id': cart.id,
        },
    })


def start_payment_process(params):
    """
    This is the implemention of this interface point.
    Here, the user has clicked the purchase (or whatever label) button
    and is beginning the payment process. This implementation will call out
    to the SaferPay API to get a redirect URL for us to drive the user to
    in order to fill out the payment information
    """
    order_id = params['order_id']
    callback_url_domain = params['site_base_url']

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        raise CCProcessorDataException(_("Could not find a corresponding order number."))

    # build out a description field that will get shown to the user in the
    # payment page on SaferPay
    description = ''
    for item in order.orderitem_set.all():
        description += item.line_desc + '\n'

    data = {
        'AMOUNT': int(order.total_cost * 100),
        'CURRENCY': order.currency.upper(),
        'DESCRIPTION': description,
        'LANGID': 'en',
        'ALLOWCOLLECT': 'no',
        'DELIVERY': 'no',
        'ACCOUNTID': settings.CC_PROCESSOR['SaferPay'].get('ACCOUNTID', ''),
        'ORDERID': settings.CC_PROCESSOR['SaferPay'].get('ORDERID_PREFIX', '') + str(order_id),
        #
        # Pass in callback links to SaferPay when the user completes the payment forms and
        # control is passed back to Open edX
        #
        'SUCCESSLINK': callback_url_domain + reverse('shoppingcart.views.postpay_callback') + '?order_id={0}'.format(order_id),
        'BACKLINK': callback_url_domain + reverse('shoppingcart.views.show_cart'),
        'FAILLINK': callback_url_domain + reverse('shoppingcart.views.show_cart'),
    }

    # SaferPay has some style definitions that can be passed in optionally
    for style in ('BODYCOLOR', 'HEADCOLOR', 'HEADLINECOLOR', 'MENUCOLOR', 'BODYFONTCOLOR', 'HEADFONTCOLOR', 'MENUFONTCOLOR', 'FONT'):
        style_value = settings.CC_PROCESSOR['SaferPay'].get(style)
        if style_value is not None:
            data[style] = style_value

    # call SaferPay's API, passing all of the parameters, and get back
    # a redirect URL which is passed back to the caller, causing a browser
    # redirect to that specified location
    response = requests.get(settings.CC_PROCESSOR['SaferPay'].get('PROCESS_URL',''), params=data)
    logger.info('Saferpay: order {0} redirected to saferpay gateway'.format(order_id))
    return {
        'redirect_url': response.content,
        'success': True,
    }


def process_postpay_callback(params):
    """
    This method is called when the user completes the SaferPay purchase page and the payment has
    been completed. For SaferPay, we need to call into a 'verify' API endpoint to fully
    authorize the transaction from the application point of view
    """

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

        # OK the transaction is legit, go ahead and book this transaction in the Order
        # which can mean that the user is registered for the course (or some other workflow)
        order.purchase(
            processor_reply_dump=json.dumps(response_data)
        )
        result['success'] = True
    else:
        result['success'] = False

    return result

