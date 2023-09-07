"""
This file contains celery tasks for notifications.
"""
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.events import notification_generated_event
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    Notification,
    get_course_notification_preference_config_version
)

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


@shared_task
@set_code_owner_attribute
def send_notifications(user_ids, course_key: str, app_name, notification_type, context, content_url):
    """
    Send notifications to the users.
    """
    course_key = CourseKey.from_string(course_key)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    user_ids = list(set(user_ids))

    # check if what is preferences of user and make decision to send notification or not
    preferences = CourseNotificationPreference.objects.filter(
        user_id__in=user_ids,
        course_id=course_key,
    )
    preferences = create_notification_pref_if_not_exists(user_ids, list(preferences), course_key)
    notifications = []
    for preference in preferences:
        preference = update_user_preference(preference, preference.user, course_key)
        if (
            preference and
            preference.get_web_config(app_name, notification_type) and
            preference.get_app_config(app_name).get('enabled', False)
        ):
            notifications.append(
                Notification(
                    user_id=preference.user_id,
                    app_name=app_name,
                    notification_type=notification_type,
                    content_context=context,
                    content_url=content_url,
                    course_id=course_key,
                )
            )
    # send notification to users but use bulk_create
    Notification.objects.bulk_create(notifications)
    notification_generated_event(user_ids, app_name, notification_type, course_key)


def update_user_preference(preference: CourseNotificationPreference, user, course_id):
    """
    Update user preference if config version is changed.
    """
    current_version = get_course_notification_preference_config_version()
    if preference.config_version != current_version:
        return preference.get_updated_user_course_preferences(user, course_id)
    return preference


def create_notification_pref_if_not_exists(user_ids: List, preferences: List, course_id: CourseKey):
    """
    Create notification preference if not exist.
    """
    new_preferences = []

    for user_id in user_ids:
        if not any(preference.user_id == int(user_id) for preference in preferences):
            new_preferences.append(CourseNotificationPreference(
                user_id=user_id,
                course_id=course_id,
            ))
            logger.info('Creating new notification preference for user because it does not exist.')
    if new_preferences:
        # ignoring conflicts because it is possible that preference is already created by another process
        # conflicts may arise because of constraint on user_id and course_id fields in model
        CourseNotificationPreference.objects.bulk_create(new_preferences, ignore_conflicts=True)
        preferences = preferences + new_preferences
    return preferences
