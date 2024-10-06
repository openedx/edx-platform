"""
This file contains celery tasks for notifications.
"""
from datetime import datetime, timedelta
from typing import List

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey
from pytz import UTC

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.audience_filters import NotificationFilter
from openedx.core.djangoapps.notifications.base_notification import (
    get_default_values_of_preference,
    get_notification_content
)
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATION_GROUPING, ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.events import notification_generated_event
from openedx.core.djangoapps.notifications.grouping_notifications import (
    get_user_existing_notifications,
    group_user_notifications, NotificationRegistry,
)
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    Notification,
    get_course_notification_preference_config_version
)
from openedx.core.djangoapps.notifications.utils import clean_arguments, get_list_in_batches


logger = get_task_logger(__name__)


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
@transaction.atomic
def create_course_notification_preferences_for_courses(self, course_ids):
    """
    This task creates Course Notification Preferences for users in courses.
    """
    newly_created = 0
    for course_id in course_ids:
        enrollments = CourseEnrollment.objects.filter(course_id=course_id, is_active=True)
        logger.debug(f'Found {enrollments.count()} enrollments for course {course_id}')
        logger.debug(f'Creating Course Notification Preferences for course {course_id}')
        for enrollment in enrollments:
            _, created = CourseNotificationPreference.objects.get_or_create(
                user=enrollment.user, course_id=course_id
            )
            if created:
                newly_created += 1

        logger.debug(
            f'CourseNotificationPreference back-fill completed for course {course_id}.\n'
            f'Newly created course preferences: {newly_created}.\n'
        )


@shared_task(ignore_result=True)
@set_code_owner_attribute
def delete_notifications(kwargs):
    """
    Delete notifications
    kwargs: dict {notification_type, app_name, created, course_id}
    """
    batch_size = settings.EXPIRED_NOTIFICATIONS_DELETE_BATCH_SIZE
    total_deleted = 0
    kwargs = clean_arguments(kwargs)
    logger.info(f'Running delete with kwargs {kwargs}')
    while True:
        ids_to_delete = Notification.objects.filter(
            **kwargs
        ).values_list('id', flat=True)[:batch_size]
        ids_to_delete = list(ids_to_delete)
        if not ids_to_delete:
            break
        delete_queryset = Notification.objects.filter(
            id__in=ids_to_delete
        )
        delete_count, _ = delete_queryset.delete()
        total_deleted += delete_count
    logger.info(f'Total deleted: {total_deleted}')


@shared_task(ignore_result=True)
@set_code_owner_attribute
def delete_expired_notifications():
    """
    This task deletes all expired notifications
    """
    batch_size = settings.EXPIRED_NOTIFICATIONS_DELETE_BATCH_SIZE
    expiry_date = datetime.now(UTC) - timedelta(days=settings.NOTIFICATIONS_EXPIRY)
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

    if not is_notification_valid(notification_type, context):
        raise ValidationError(f"Notification is not valid {app_name} {notification_type} {context}")

    user_ids = list(set(user_ids))
    batch_size = settings.NOTIFICATION_CREATION_BATCH_SIZE
    group_by_id = context.pop('group_by_id', '')
    grouping_function = NotificationRegistry.get_grouper(notification_type)
    waffle_flag_enabled = ENABLE_NOTIFICATION_GROUPING.is_enabled(course_key)
    grouping_enabled = waffle_flag_enabled and group_by_id and grouping_function is not None
    notifications_generated = False
    notification_content = ''
    sender_id = context.pop('sender_id', None)
    default_web_config = get_default_values_of_preference(app_name, notification_type).get('web', False)
    generated_notification_audience = []

    for batch_user_ids in get_list_in_batches(user_ids, batch_size):
        logger.debug(f'Sending notifications to {len(batch_user_ids)} users in {course_key}')
        batch_user_ids = NotificationFilter().apply_filters(batch_user_ids, course_key, notification_type)
        logger.debug(f'After applying filters, sending notifications to {len(batch_user_ids)} users in {course_key}')

        existing_notifications = (
            get_user_existing_notifications(batch_user_ids, notification_type, group_by_id, course_key))\
            if grouping_enabled else {}

        # check if what is preferences of user and make decision to send notification or not
        preferences = CourseNotificationPreference.objects.filter(
            user_id__in=batch_user_ids,
            course_id=course_key,
        )
        preferences = list(preferences)

        if default_web_config:
            preferences = create_notification_pref_if_not_exists(batch_user_ids, preferences, course_key)

        if not preferences:
            continue

        notifications = []
        for preference in preferences:
            user_id = preference.user_id
            preference = update_user_preference(preference, user_id, course_key)

            if (
                preference and
                preference.is_enabled_for_any_channel(app_name, notification_type) and
                preference.get_app_config(app_name).get('enabled', False)
            ):
                notification_preferences = preference.get_channels_for_notification_type(app_name, notification_type)
                new_notification = Notification(
                    user_id=user_id,
                    app_name=app_name,
                    notification_type=notification_type,
                    content_context=context,
                    content_url=content_url,
                    course_id=course_key,
                    web='web' in notification_preferences,
                    email='email' in notification_preferences,
                    group_by_id=group_by_id,
                )
                if grouping_enabled and existing_notifications.get(user_id, None):
                    group_user_notifications(new_notification, existing_notifications[user_id])
                else:
                    notifications.append(new_notification)
                    generated_notification_audience.append(user_id)

        # send notification to users but use bulk_create
        notification_objects = Notification.objects.bulk_create(notifications)
        if notification_objects and not notifications_generated:
            notifications_generated = True
            notification_content = notification_objects[0].content

    if notifications_generated:
        notification_generated_event(
            generated_notification_audience, app_name, notification_type, course_key, content_url,
            notification_content, sender_id=sender_id
        )


def is_notification_valid(notification_type, context):
    """
    Validates notification before creation
    """
    try:
        get_notification_content(notification_type, context)
    except Exception:  # pylint: disable=broad-except
        return False
    return True


def update_user_preference(preference: CourseNotificationPreference, user_id, course_id):
    """
    Update user preference if config version is changed.
    """
    current_version = get_course_notification_preference_config_version()
    if preference.config_version != current_version:
        return preference.get_user_course_preference(user_id, course_id)
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
    if new_preferences:
        # ignoring conflicts because it is possible that preference is already created by another process
        # conflicts may arise because of constraint on user_id and course_id fields in model
        CourseNotificationPreference.objects.bulk_create(new_preferences, ignore_conflicts=True)
        preferences = preferences + new_preferences
    return preferences
