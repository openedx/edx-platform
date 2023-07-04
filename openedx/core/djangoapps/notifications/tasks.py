"""
This file contains celery tasks for notifications.
"""
from datetime import datetime, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute
from pytz import UTC

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, Notification

logger = get_task_logger(__name__)


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
@transaction.atomic
def create_course_notification_preferences_for_courses(self, course_ids):
    """
    This task creates Course Notification Preferences for users in courses.
    """
    logger.info('Running task create_course_notification_preferences')
    newly_created = 0
    for course_id in course_ids:
        enrollments = CourseEnrollment.objects.filter(course_id=course_id, is_active=True)
        logger.info(f'Found {enrollments.count()} enrollments for course {course_id}')
        logger.info(f'Creating Course Notification Preferences for course {course_id}')
        for enrollment in enrollments:
            _, created = CourseNotificationPreference.objects.get_or_create(
                user=enrollment.user, course_id=course_id
            )
            if created:
                newly_created += 1

        logger.info(
            f'CourseNotificationPreference back-fill completed for course {course_id}.\n'
            f'Newly created course preferences: {newly_created}.\n'
        )
    logger.info('Completed task create_course_notification_preferences')


@shared_task(ignore_result=True)
@set_code_owner_attribute
def delete_expired_notifications():
    """
    This task deletes all expired notifications
    """
    batch_size = settings.EXPIRED_NOTIFICATIONS_DELETE_BATCH_SIZE
    expiry_date = datetime.now(UTC) - timedelta(days=settings.NOTIFICATIONS_EXPIRY)
    logger.info(f'Deleting expired notifications with batch size: {batch_size}')
    start_time = datetime.now()
    total_deleted = 0
    delete_count = None
    while delete_count != 0:
        batch_start_time = datetime.now()
        ids_to_delete = Notification.objects.filter(
            created__lte=expiry_date,
        ).values_list('id', flat=True)[:batch_size]
        ids_to_delete = list(ids_to_delete)
        delete_queryset = Notification.objects.filter(
            id__in=ids_to_delete
        )
        delete_count, _ = delete_queryset.delete()
        total_deleted += delete_count
        time_elapsed = datetime.now() - batch_start_time
        logger.info(f'{delete_count} Notifications deleted in current batch in {time_elapsed} seconds.')
    time_elapsed = datetime.now() - start_time
    logger.info(f'{total_deleted} Notifications deleted in {time_elapsed} seconds.')
