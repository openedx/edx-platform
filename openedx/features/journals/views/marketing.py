""" Journal bundle about page's view """
from django.conf import settings
from django.contrib.auth.models import User
from django.http import Http404

from edxmako.shortcuts import render_to_response
from openedx.core.djangoapps.catalog.models import CatalogIntegration
from openedx.core.djangoapps.commerce.utils import ecommerce_api_client
from openedx.features.journals.api import get_journal_bundles, get_journals_root_url
from lms.djangoapps.commerce.utils import EcommerceService


def bundle_about(request, bundle_uuid):
    """
    Journal bundle about page's view.
    """
    bundle = get_journal_bundles(request.site, bundle_uuid=bundle_uuid)
    if not bundle:
        raise Http404
    bundle = bundle[0]  # get_journal_bundles always returns list of bundles
    bundle = extend_bundle(bundle)
    context = {
        'journals_root_url': get_journals_root_url(),
        'discovery_root_url': CatalogIntegration.current().get_internal_api_url(),
        'bundle': bundle,
        'uses_bootstrap': True,
    }
    return render_to_response('journals/bundle_about.html', context)


def extend_bundle(bundle):
    """
    Extend the pricing data in journal bundle.
    """
    applicable_seat_types = bundle['applicable_seat_types']
    matching_seats = [
        get_matching_seat(course, applicable_seat_types)
        for course in bundle['courses']
    ]
    # Remove `None`s from above.
    matching_seats = [seat for seat in matching_seats if seat]
    course_skus = [seat['sku'] for seat in matching_seats]
    journal_skus = [journal['sku'] for journal in bundle['journals']]
    all_skus = course_skus + journal_skus
    pricing_data = get_pricing_data(all_skus)
    bundle.update({
        'pricing_data': pricing_data
    })
    return bundle


def get_matching_seat(course, seat_types):
    """ Filtered out the course runs on the bases of applicable_seat_types """
    for course_run in course['course_runs']:
        for seat in course_run['seats']:
            if seat['type'] in seat_types:
                return seat


def get_pricing_data(skus):
    """
    Get the pricing data from ecommerce for given skus.
    """
    user = User.objects.get(username=settings.ECOMMERCE_SERVICE_WORKER_USERNAME)
    api = ecommerce_api_client(user)
    pricing_data = api.baskets.calculate.get(sku=skus, is_anonymous=True)
    discount_value = float(pricing_data['total_incl_tax_excl_discounts']) - float(pricing_data['total_incl_tax'])
    ecommerce_service = EcommerceService()
    purchase_url = ecommerce_service.get_checkout_page_url(*skus)
    pricing_data.update({
        'is_discounted': pricing_data['total_incl_tax'] != pricing_data['total_incl_tax_excl_discounts'],
        'discount_value': discount_value,
        'purchase_url': purchase_url,
    })
    return pricing_data
