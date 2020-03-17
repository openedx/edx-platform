"""
Tasks for the "ecommerce" module of "UCSDFeatures" app
"""
from celery.task import task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User

from openedx.features.ucsd_features.ecommerce.ecommerce_client import EcommerceRestAPIClient


logger = get_task_logger(__name__)


@task()
def assign_course_voucher_to_user(user_email, course_key, course_sku):
    """
    This task is responsible for sending the request to Ecommerce to
    assign a voucher to the user for the course.

    Arguments:
        user_email (str): email of the user to whom the voucher is to be assigned
        course_key (str): course_key of the course for which the voucher is to be assigned
        course_sku (str): SKU of the course for which the voucher is to be assigned
    """
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        logger.error('User with email: {} not found. Cannot assign a voucher.'.format(user_email))
        return

    ecommerce_client = EcommerceRestAPIClient(user=user)
    is_voucher_assigned, message = ecommerce_client.assign_voucher_to_user(
        user=user, course_key=course_key, course_sku=course_sku
    )
    if is_voucher_assigned:
        logger.info('Successfully assigned a voucher to '
                    'user {username} for the course {course_key}.'.format(
                        username=user.username,
                        course_key=course_key,
                    ))
    else:
        logger.error('Failed to send request to assign a voucher to '
                     'user {username} for the course {course_key}.'
                     '\nError message: {message}'.format(
                         username=user.username,
                         course_key=course_key,
                         message=message
                     ))
