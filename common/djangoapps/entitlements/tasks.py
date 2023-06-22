"""
This file contains celery tasks for entitlements-related functionality.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings  # lint-amnesty, pylint: disable=unused-import
from edx_django_utils.monitoring import set_code_owner_attribute

from common.djangoapps.entitlements.models import CourseEntitlement, CourseEntitlementSupportDetail

LOGGER = get_task_logger(__name__)

# Maximum number of retries before giving up on awarding credentials.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def expire_old_entitlements(self, start, end, logid='...'):
    """
    This task is designed to be called to process a bundle of entitlements
    that might be expired and confirm if we can do so. This is useful when
    checking if an entitlement has just been abandoned by the learner and needs
    to be expired. (In the normal course of a learner using the platform, the
    entitlement will expire itself. But if a learner doesn't log in... So we
    run this task every now and then to clear the backlog.)

    Args:
        start (int): The beginning id in the database to examine
        end (int): The id in the database to stop examining at (i.e. range is exclusive)
        logid (str): A string to identify this task in the logs

    Returns:
        None

    """
    LOGGER.info('Running task expire_old_entitlements %d:%d [%s]', start, end, logid)

    # This query could be optimized to return a more narrow set, but at a
    # complexity cost. See bug LEARNER-3451 about improving it.
    entitlements = CourseEntitlement.objects.filter(expired_at__isnull=True, id__gte=start, id__lte=end)

    countdown = 2 ** self.request.retries

    try:
        for entitlement in entitlements:
            # This property request will update the expiration if necessary as
            # a side effect. We could manually call update_expired_at(), but
            # let's use the same API the rest of the LMS does, to mimic normal
            # usage and allow the update call to be an internal detail.
            if entitlement.expired_at_datetime:
                LOGGER.info('Expired entitlement with id %d [%s]', entitlement.id, logid)

    except Exception as exc:
        LOGGER.exception('Failed to expire entitlements [%s]', logid)
        # The call above is idempotent, so retry at will
        raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)

    LOGGER.info('Successfully completed the task expire_old_entitlements after examining %d entries [%s]', entitlements.count(), logid)  # lint-amnesty, pylint: disable=line-too-long


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def expire_and_create_entitlements(self, entitlements, support_user):
    """
    Expire entitlements older than one year.

    Exception: if the entitlement is for a course in a list of exceptional courses,
    expire those entitlements if they're older than 18 months instead.

    Then create a copy of the expired entitlement to renew it for another year
    / 18 months.

    Args:
        entitlements (QuerySet): A QuerySet with the entitlements to expire.
        support_user (django.contrib.auth.models.user): The username to attribute
        the entitlement expiration and recreation to.

    Returns:
        None

    """
    LOGGER.info('Running task expire_and_create_entitlements')

    try:
        for entitlement in entitlements:
            LOGGER.info('Started expiring entitlement with id %d', entitlement.id)
            entitlement.expire_entitlement()
            LOGGER.info('Expired entitlement with id %d as expiration period has reached', entitlement.id)
            support_detail = {
                'action': 'EXPIRED',
                'comments': 'REV-3574',
                'entitlement': entitlement,
                'support_user': support_user,
            }
            CourseEntitlementSupportDetail.objects.create(**support_detail)

            # Creating new entitlement and support details
            new_entitlement = {
                'course_uuid': entitlement.course_uuid,
                'user': entitlement.user,
                'mode': entitlement.mode,
                'refund_locked': True,
            }
            CourseEntitlement.objects.create(**new_entitlement)
            support_detail = {
                'action': 'CREATE',
                'comments': 'REV-3574',
                'entitlement': entitlement,
                'support_user': support_user,
            }
            CourseEntitlementSupportDetail.objects.create(**support_detail)
            LOGGER.info('created new entitlement with id %d in a correspondence of above expired entitlement', new_entitlement.id)  # lint-amnesty, pylint: disable=line-too-long

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception('Failed to expire entitlements that reached their expiration period')

    LOGGER.info('Successfully completed the task expire_and_create_entitlements after examining %d entries', entitlements.count())  # lint-amnesty, pylint: disable=line-too-long
