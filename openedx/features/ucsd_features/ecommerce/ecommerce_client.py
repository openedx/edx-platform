"""
Custom client to communicate with ecommerce service
"""
import logging

from openedx.core.djangoapps.commerce.utils import ecommerce_api_client


logger = logging.getLogger(__name__)


class EcommerceRestAPIClient:
    """
    Client that communicates with the Ecommerce service
    """

    def __init__(self, user, session=None):
        """
        Initialize the ecommerce client for the current user and session

        Arguments:
            user: User object
            session: Current user's session
        """

        self.client = ecommerce_api_client(user, session)

    def assign_voucher_to_user(self, user, course_key, course_sku=None):
        """
        Sends request to Ecommerce to assign a voucher to the user for the course.

        Arguments:
            user: User object
            course_key (str): course_key of the course for which the voucher is to be assigned
            course_sku (str): SKU of the course for which the voucher is to be assigned

        Returns:
            True: '' (Tuple): if voucher is successfully assigned
            False: <ERROR_MESSAGE> (Tuple): if voucher could not be assigned
        """
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
        """
        Sends request to check if a coupon is available for the course

        Arguments:
            course_key (str): course_key of the course for which the coupon is to be checked for availability

        Returns:
            True: if coupon is available for the course
            False: if coupon is not available for the course
        """
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
