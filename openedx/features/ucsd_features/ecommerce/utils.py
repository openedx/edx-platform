"""
Util methods related to Open edX e-commerce service
"""
import logging

from django.conf import settings

from openedx.features.ucsd_features.ecommerce.EcommerceClient import EcommerceRestAPIClient


logger = logging.getLogger(__name__)


def is_user_eligible_for_discount(request, course_key):
    if not settings.FEATURES.get('ENABLE_GEOGRAPHIC_DISCOUNTS', False):
        logger.info('Geographics discounts are not enabled hence skipping further processing.')
        return False

    country_code = request.session.get('country_code', None)
    ecommerce_client = EcommerceRestAPIClient(user=request.user)

    if country_code not in settings.COUNTRIES_ELIGIBLE_FOR_DISCOUNTS:
        return False

    return ecommerce_client.check_coupon_availability_for_course(course_key)
