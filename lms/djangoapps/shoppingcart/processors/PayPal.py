import json
from django.conf import settings
from django.core.urlresolvers import reverse
from edxmako.shortcuts import render_to_string
from shoppingcart.processors.helpers import get_processor_config
from shoppingcart.models import Order

import logging

log = logging.getLogger(__name__)


def render_purchase_form_html(cart, callback_url=''):
    from shoppingcart.views import verify_for_closed_enrollment
    shoppingcart_items = verify_for_closed_enrollment(cart.user, cart)[-1]
    description = [("Payment for course '{}'\n".format(course.display_name)) for item, course in shoppingcart_items]
    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': get_processor_config().get('ACTION'),
        'params': {
            'cmd': '_xclick',
            'charset': 'utf-8',
            'currency_code': cart.currency.upper(),
            'amount': cart.total_cost,
            'item_name': "".join(description)[0:127],
            'custom': cart.id,
            'business': get_processor_config().get('CLIENT_ID'),
            'notify_url': callback_url,
            'cancel_return': 'http://{}{}'.format(settings.SITE_NAME, reverse('shoppingcart.views.show_cart')),
            'return': 'http://{}{}'.format(settings.SITE_NAME, reverse('dashboard')),
        }
    })


def process_postpay_callback(params):
    if params['payment_status'] == 'Completed':
        order = Order.objects.get(id=int(params['custom']))
        log.info('Order "{}" and transaction "{}" is successed'.format(order, params['txn_id']))
        order.purchase(
            country=params.get('address_country'),
            first=params.get('first_name'),
            last=params.get('last_name'),
            street1=params.get('address_street'),
            city=params.get('address_city'),
            state=params.get('address_state'),
            postalcode=params.get('address_zip'),
            processor_reply_dump=json.dumps(params)
        )
        return {'success': True, 'order': order, 'error_html': ''}
    else:
        log.error('Order "{}" and transaction "{}" is failed'.format(order, params['txn_id']))
        return {'success': False, 'order': order, 'error_html': 'Transaction "{}" is filed'.format(params['txn_id'])}
