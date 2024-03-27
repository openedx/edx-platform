"""
Celery tasks for sending email notifications
"""
from celery import shared_task
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx.core.djangoapps.notifications.models import CourseNotificationPreference, Notification
from .message_type import EmailNotificationMessageType
from .utils import (
    create_app_notifications_dict,
    create_email_digest_context,
    get_start_end_date,
    is_email_notification_flag_enabled
)


def get_audience_for_cadence_email(cadence_type):
    """
    Returns users that are eligible to receive cadence email
    """
    if cadence_type not in ["Daily", "Weekly"]:
        raise ValueError("Invalid value for parameter cadence_type")
    start_date, end_date = get_start_end_date(cadence_type)
    users = Notification.objects.filter(
        created__gte=start_date,
        created__lte=end_date
    ).values_list('user__username', flat=True).distinct()
    return users


def get_enabled_notification_types_for_cadence(user, cadence_type):
    """
    Returns dictionary of course and notification_types for which email_cadence value
    is equal to cadence_type
    """
    if cadence_type not in ["Daily", "Weekly"]:
        raise ValueError('Invalid cadence_type')
    preferences = CourseNotificationPreference.objects.filter(user=user)
    course_types = {}
    for preference in preferences:
        key = preference.course_id
        value = []
        config = preference.notification_preference_config
        for app_data in config.values():
            for notification_type, type_dict in app_data.items():
                if type_dict['email_cadence'] == cadence_type:
                    value.append(notification_type)
            if 'core' in value:
                value.remove('core')
                value.extend(app_data['core_notification_types'])
        course_types[key] = value
    return course_types


def send_digest_email_to_user(user, cadence_type, course_language='en', courses_data=None):
    """
    Send [cadence_type] email to user.
    Cadence Type can be "Daily" or "Weekly"
    """
    if cadence_type not in ["Daily", "Weekly"]:
        raise ValueError('Invalid cadence_type')
    if not is_email_notification_flag_enabled(user):
        return
    start_date, end_date = get_start_end_date(cadence_type)
    ##################################
    # TODO: get notifications for preferences with cadence_type
    ##################################
    course_ids_dict = get_enabled_notification_types_for_cadence(user, cadence_type)
    notifications = Notification.objects.none()
    for course_id, notification_types in course_ids_dict.items():
        queryset = Notification.objects.filter(user=user, course_id=course_id, notification_type__in=notification_types,
                                               created__gte=start_date, created__lte=end_date)
        notifications = notifications | queryset
    if not notifications:
        return
    apps_dict = create_app_notifications_dict(notifications)
    message_context = create_email_digest_context(apps_dict, start_date, end_date, cadence_type,
                                                  courses_data=courses_data)
    recipient = Recipient(user.id, user.email)
    message = EmailNotificationMessageType(
        app_label="notifications", name="email_digest"
    ).personalize(recipient, course_language, message_context)
    ace.send(message)


@shared_task(ignore_result=True)
@set_code_owner_attribute
def send_digest_email_to_all_users(cadence_type):
    """
    Send email digest to all eligible users
    """
    users = get_audience_for_cadence_email(cadence_type)
    courses_data = {}
    for user in users:
        send_digest_email_to_user(user, cadence_type, courses_data=courses_data)
