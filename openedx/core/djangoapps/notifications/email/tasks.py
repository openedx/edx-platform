"""
Celery tasks for sending email notifications
"""
from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _, override as translation_override
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    Notification,
    get_course_notification_preference_config_version
)
from .events import send_user_email_digest_sent_event
from .message_type import EmailNotificationMessageType
from .utils import (
    add_headers_to_email_message,
    create_app_notifications_dict,
    create_email_digest_context,
    create_email_template_context,
    filter_notification_with_email_enabled_preferences,
    get_course_info,
    get_language_preference_for_users,
    get_start_end_date,
    get_text_for_notification_type,
    get_unique_course_ids,
    is_email_notification_flag_enabled,
)


User = get_user_model()
logger = get_task_logger(__name__)


def get_audience_for_cadence_email(cadence_type):
    """
    Returns users that are eligible to receive cadence email
    """
    if cadence_type not in [EmailCadence.DAILY, EmailCadence.WEEKLY]:
        raise ValueError("Invalid value for parameter cadence_type")
    start_date, end_date = get_start_end_date(cadence_type)
    user_ids = Notification.objects.filter(
        email=True,
        created__gte=start_date,
        created__lte=end_date
    ).values_list('user__id', flat=True).distinct()
    users = User.objects.filter(id__in=user_ids)
    return users


def get_user_preferences_for_courses(course_ids, user):
    """
    Returns updated user preference for course_ids
    """
    # Create new preferences
    new_preferences = []
    preferences = CourseNotificationPreference.objects.filter(user=user, course_id__in=course_ids)
    preferences = list(preferences)
    for course_id in course_ids:
        if not any(preference.course_id == course_id for preference in preferences):
            pref = CourseNotificationPreference(user=user, course_id=course_id)
            new_preferences.append(pref)
    if new_preferences:
        CourseNotificationPreference.objects.bulk_create(new_preferences, ignore_conflicts=True)
    # Update preferences to latest config version
    current_version = get_course_notification_preference_config_version()
    for preference in preferences:
        if preference.config_version != current_version:
            preference = preference.get_user_course_preference(user.id, preference.course_id)
        new_preferences.append(preference)
    return new_preferences


def send_digest_email_to_user(user, cadence_type, start_date, end_date, user_language='en', courses_data=None):
    """
    Send [cadence_type] email to user.
    Cadence Type can be EmailCadence.DAILY or EmailCadence.WEEKLY
    start_date: Datetime object
    end_date: Datetime object
    """
    if cadence_type not in [EmailCadence.DAILY, EmailCadence.WEEKLY]:
        raise ValueError('Invalid cadence_type')
    logger.info(f'<Email Cadence> Sending email to user {user.username} ==Temp Log==')
    if not user.has_usable_password():
        logger.info(f'<Email Cadence> User is disabled {user.username} ==Temp Log==')
        return
    if not is_email_notification_flag_enabled(user):
        logger.info(f'<Email Cadence> Flag disabled for {user.username} ==Temp Log==')
        return
    notifications = Notification.objects.filter(user=user, email=True,
                                                created__gte=start_date, created__lte=end_date)
    if not notifications:
        logger.info(f'<Email Cadence> No notification for {user.username} ==Temp Log==')
        return

    with translation_override(user_language):
        course_ids = get_unique_course_ids(notifications)
        preferences = get_user_preferences_for_courses(course_ids, user)
        notifications = filter_notification_with_email_enabled_preferences(notifications, preferences, cadence_type)
        if not notifications:
            logger.info(f'<Email Cadence> No filtered notification for {user.username} ==Temp Log==')
            return
        apps_dict = create_app_notifications_dict(notifications)
        message_context = create_email_digest_context(apps_dict, user.username, start_date, end_date,
                                                      cadence_type, courses_data=courses_data)
        recipient = Recipient(user.id, user.email)
        message = EmailNotificationMessageType(
            app_label="notifications", name="email_digest"
        ).personalize(recipient, user_language, message_context)
        message = add_headers_to_email_message(message, message_context)
        message.options['skip_disable_user_policy'] = True
        ace.send(message)
        send_user_email_digest_sent_event(user, cadence_type, notifications, message_context)
        logger.info(f'<Email Cadence> Email sent to {user.username} ==Temp Log==')


@shared_task(ignore_result=True)
@set_code_owner_attribute
def send_digest_email_to_all_users(cadence_type):
    """
    Send email digest to all eligible users
    """
    logger.info(f'<Email Cadence> Sending cadence email of type {cadence_type}')
    users = get_audience_for_cadence_email(cadence_type)
    language_prefs = get_language_preference_for_users([user.id for user in users])
    courses_data = {}
    start_date, end_date = get_start_end_date(cadence_type)
    logger.info(f'<Email Cadence> Email Cadence Audience {len(users)}')
    for user in users:
        user_language = language_prefs.get(user.id, 'en')
        send_digest_email_to_user(user, cadence_type, start_date, end_date, user_language=user_language,
                                  courses_data=courses_data)


def send_immediate_cadence_email(email_notification_mapping, course_key):
    """
    Send immediate cadence email to users
    Parameters:
        email_notification_mapping: Dictionary of user_id and Notification object
        course_key: Course key for which the email is sent
    """
    if not email_notification_mapping:
        return
    user_list = email_notification_mapping.keys()
    users = User.objects.filter(id__in=user_list)
    language_prefs = get_language_preference_for_users(user_list)
    course_name = get_course_info(course_key).get("name", course_key)
    for user in users.iterator(chunk_size=100):
        if not user.has_usable_password():
            logger.info(f'<Immediate Email> User is disabled {user.username}')
            continue
        if not is_email_notification_flag_enabled(user):
            logger.info(f'<Immediate Email> Flag disabled for {user.username}')
            continue
        notification = email_notification_mapping.get(user.id, None)
        if not notification:
            logger.info(f'<Immediate Email> No notification for {user.username}')
            continue

        language = language_prefs.get(user.id, 'en')
        with translation_override(language):
            soup = BeautifulSoup(notification.content, "html.parser")
            title = _("New Course Update") if notification.notification_type == "course_updates" else soup.get_text()
            message_context = create_email_template_context(user.username)
            message_context.update({
                "course_id": course_key,
                "course_name": course_name,
                "content_url": notification.content_url,
                "content_title": title,
                "footer_email_reason": _(
                    "You are receiving this email because you are enrolled in the edX course "
                ) + str(course_name),
                "content": notification.content_context.get("email_content", notification.content),
                "view_text": get_text_for_notification_type(notification.notification_type),
            })
            message = EmailNotificationMessageType(
                app_label="notifications", name="immediate_email"
            ).personalize(Recipient(user.id, user.email), language, message_context)
            message = add_headers_to_email_message(message, message_context)
            ace.send(message)
