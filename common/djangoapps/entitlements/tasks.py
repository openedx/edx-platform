"""
This file contains celery tasks for entitlements-related functionality.
"""
from datetime import date
from dateutil.relativedelta import relativedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings  # lint-amnesty, pylint: disable=unused-import
from edx_django_utils.monitoring import set_code_owner_attribute

from common.djangoapps.entitlements.models import CourseEntitlement
from common.djangoapps.entitlements.rest_api.v1.views import EntitlementViewSet

LOGGER = get_task_logger(__name__)

# Maximum number of retries before giving up on awarding credentials.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11
#course uuids for which entitlements should be expired after 18 months.
MIT_SUPPLY_CHAIN_COURSES = [
    '0d9b47982e3d486aa3189a7035bbda77',
    '09532745c837467b9078093b8e1265a8',
    '324970b703a444d7b39e10bbda6f119f',
    '5f1c55b4354e4155af4a76450953e10d',
    'ed927a1a4a95415ba865c3d722ac549c',
    '6513ed9c112a495182ad7036cbe52831',
]

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
def expire_and_create_entitlements(self, no_of_entitlements):
    """
    This task is designed to be called to process and expire bundle of entitlements
    that are older than one year on in exceptional case 18 months.

    Args:
        None

    Returns:
        None

    """
    LOGGER.info('Running task expire_and_create_entitlements')

    current_date = date.today()
    expiration_period = current_date - relativedelta(years=1)
    exceptional_expiration_period = current_date - relativedelta(years=1, months=6)
    normal_entitlements = CourseEntitlement.objects.filter(expired_at__isnull=True,
                                                           created__lte=expiration_period).exclude(course_uuid__in=MIT_SUPPLY_CHAIN_COURSES)
    exceptional_entitlements = CourseEntitlement.objects.filter(expired_at__isnull=True,
                                                                created__lte=exceptional_expiration_period, course_uuid__in=MIT_SUPPLY_CHAIN_COURSES)
   
    entitlements = normal_entitlements | exceptional_entitlements

    countdown = 2 ** self.request.retries


    try:
        for entitlement in entitlements[:no_of_entitlements]:

            entitlement.expire_entitlement()
            LOGGER.info('Expired entitlement with id %d ', entitlement.id)
            entitlement.pk = None
            entitlement.expired_at = None
            entitlement.modified = None
            entitlement.save()
            LOGGER.info('created new entitlement with id %d ', entitlement.id)


    except Exception as exc:
        LOGGER.exception('Failed to expire entitlements ',)
        # The call above is idempotent, so retry at will
        raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)

    LOGGER.info('Successfully completed the task expire_and_create_entitlements after examining %d entries', entitlements.count())  # lint-amnesty, pylint: disable=line-too-long
