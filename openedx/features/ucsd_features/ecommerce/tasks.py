from celery.task import task
from celery.utils.log import get_task_logger
from django.contrib.auth.models import User

from openedx.features.ucsd_features.ecommerce.EcommerceClient import EcommerceRestAPIClient


logger = get_task_logger(__name__)


@task()
def assign_course_voucher_to_user(user_email, course_key, course_sku):
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
