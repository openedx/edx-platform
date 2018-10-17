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
    description = [('Payment for course "{}"\n'.format(course.display_name)) for item, course in shoppingcart_items]
    return render_to_string('shoppingcart/cybersource_form.html', {
        'action': get_processor_config().get('action'),
        'params': {
            'agent_id': get_processor_config().get('agent_id'),
            'tx': cart.id,
            'amount': cart.total_cost,
            'item_name': "".join(description),
            'callback': callback_url,
            'return': callback_url,
            'cancel': 'http://{}{}'.format(settings.SITE_NAME, reverse('shoppingcart.views.show_cart')),
            'currency_code': cart.currency.upper()
        }
    })


def process_postpay_callback(params):
    if params['x_status'] == '1':
        order = Order.objects.get(id=int(params['tx']))
        log.info('Order "{}" and transaction "{}" is successed'.format(order, params['x_trans_id']))
        order.purchase(
            country=u'Uganda',
            processor_reply_dump=json.dumps(params)
        )
        return {'success': True, 'order': order, 'error_html': ''}
    else:
        log.error('Order "{}" and transaction "{}" is failed'.format(order, params['x_trans_id']))
        return {'success': False, 'order': order, 'error_html': 'Transaction "{}" is filed'.format(params['x_trans_id'])}
