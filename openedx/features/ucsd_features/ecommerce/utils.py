"""
Util methods related to Open edX e-commerce service
"""
import logging

from django.conf import settings

from openedx.features.ucsd_features.ecommerce.ecommerce_client import EcommerceRestAPIClient


logger = logging.getLogger(__name__)


def is_user_eligible_for_discount(request, course_key):
    """
    Checks if the user in the request is eligible to get a discount voucher for course with course_key.
    A user is eligible for discount iff:
        - ENABLE_GEOGRAPHIC_DISCOUNTS feature flag is set to True
        - User's country_code is in the list of discount eligible countries (configured through
          COUNTRIES_ELIGIBLE_FOR_DISCOUNTS setting)
        - Course matching the course_key has a Discount Coupon created on the E-commerce side


    Arguments:
        request: Request object
        course_key (str): course_key of the course for which the discount eligibility is to be checked
    """
    if not settings.FEATURES.get('ENABLE_GEOGRAPHIC_DISCOUNTS', False):
        logger.info('Geographics discounts are not enabled hence skipping further processing.')
        return False

    country_code = request.session.get('country_code', None)
    ecommerce_client = EcommerceRestAPIClient(user=request.user)

    if country_code not in settings.COUNTRIES_ELIGIBLE_FOR_DISCOUNTS:
        return False

    return ecommerce_client.check_coupon_availability_for_course(course_key)
