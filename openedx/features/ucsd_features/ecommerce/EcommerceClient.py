"""
Custom client to communicate with ecommerce service
"""
import logging

from openedx.core.djangoapps.commerce.utils import ecommerce_api_client


logger = logging.getLogger(__name__)


class EcommerceRestAPIClient:
    def __init__(self, user, session=None):
        self.client = ecommerce_api_client(user, session)

    def assign_voucher_to_user(self, user, course_key, course_sku=None):
        try:
            self.client.resource('/ucsd/api/v1/assign_voucher').post(
                {
                    'username': user.username,
                    'user_email': user.email,
                    'course_key': str(course_key),
                    'course_sku': course_sku
                })
            return True, ''
        except Exception as ex:
            logger.exception('Got failure response from ecommerce while '
                             'trying to assign a voucher to user.\n'
                             'Details:{}'.format(ex.message))
            return False, ex.message

    def check_coupon_availability_for_course(self, course_key):
        try:
            self.client.resource('/ucsd/api/v1/check_course_coupon').post(
                {
                    'course_key': course_key
                }
            )
            return True
        except Exception as ex:
            logger.exception('Got failure response from ecommerce while '
                             'trying to check coupon availability for the course.\n'
                             'Details:{}'.format(ex.message))
            return False
