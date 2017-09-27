# pylint: disable=bad-continuation
"""
Certificate Shipping Information view.
"""
import json
import logging

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from edxmako.shortcuts import render_to_response

from experiments.models import ExperimentData

log = logging.getLogger(__name__)
PHYSICAL_CERTIFICATE_EXPERIMENT_ID = 100
PHYSICAL_CERTIFICATE_EXPERIMENT_KEY = "shipping_information"


@login_required
def shipping_information(request, template_name='certificates/shipping_information.html'):
    default_shipping_json = {
        'first_name': "",
        'last_name': "",
        'address': "",
        'city': "",
        'state': "",
        'zip_code': ""
    }
    if request.method == 'GET':
        shipping_information, created = ExperimentData.objects.get_or_create(
            user=request.user,
            experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
            key=PHYSICAL_CERTIFICATE_EXPERIMENT_KEY,
            defaults={'value': json.dumps(default_shipping_json)},
        )

        shipping_json = json.loads(shipping_information.value)

    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip_code = request.POST.get('zip_code')

        shipping_json = {
            'first_name': first_name,
            'last_name': last_name,
            'address': address,
            'city': city,
            'state': state,
            'zip_code': zip_code
        }

        shipping_information = ExperimentData.objects.get(
            user=request.user,
            experiment_id=PHYSICAL_CERTIFICATE_EXPERIMENT_ID,
            key=PHYSICAL_CERTIFICATE_EXPERIMENT_KEY
        )

        shipping_information.value = json.dumps(shipping_json)
        shipping_information.save()

    return render_to_response(template_name, {'object': shipping_json})
