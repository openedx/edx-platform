"""
Celery tasks for sending email notifications
"""
from datetime import datetime, timedelta

from bs4 import BeautifulSoup
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _, override as translation_override
from django.utils import timezone
from edx_ace import ace
from edx_ace.recipient import Recipient
from edx_django_utils.monitoring import set_code_owner_attribute

from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.models import (
    Notification,
    NotificationPreference,
)
from .events import send_immediate_email_digest_sent_event, send_user_email_digest_sent_event
from .message_type import EmailNotificationMessageType
from .utils import (
    add_headers_to_email_message,
    create_app_notifications_dict,
    create_email_digest_context,
    create_email_template_context,
    filter_email_enabled_notifications,
    get_course_info,
    get_language_preference_for_users,
    get_start_end_date,
    get_text_for_notification_type,
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


@shared_task
def send_digest_email_to_user_async(user_id, cadence_type, start_date, end_date, user_language='en', courses_data=None):
    """
    Async wrapper for send_digest_email_to_user
    """
    user = get_user_model().objects.get(id=user_id)
    send_digest_email_to_user(
        user,
        cadence_type,
        start_date,
        end_date,
        user_language=user_language,
        courses_data=courses_data
    )


def send_digest_email_to_user(
    user: User,
    cadence_type: str,
    start_date: datetime,
    end_date: datetime,
    user_language: str = 'en',
    courses_data: dict = None
):
    """
    Send [cadence_type] email to user.
    Cadence Type can be EmailCadence.DAILY or EmailCadence.WEEKLY
    start_date: Datetime object
    end_date: Datetime object
    """

    if cadence_type not in [EmailCadence.IMMEDIATELY, EmailCadence.DAILY, EmailCadence.WEEKLY]:
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
        preferences = NotificationPreference.objects.filter(user=user)
        notifications_list = filter_email_enabled_notifications(
            notifications,
            preferences,
            user,
            cadence_type=cadence_type
        )
        if not notifications_list:
            logger.info(f'<Email Cadence> No filtered notification for {user.username} ==Temp Log==')
            return

        apps_dict = create_app_notifications_dict(notifications_list)
        message_context = create_email_digest_context(apps_dict, user.username, start_date, end_date,
                                                      cadence_type, courses_data=courses_data)
        recipient = Recipient(user.id, user.email)
        message = EmailNotificationMessageType(
            app_label="notifications", name="email_digest"
        ).personalize(recipient, user_language, message_context)
        message = add_headers_to_email_message(message, message_context)
        message.options['skip_disable_user_policy'] = True
        ace.send(message)
        notifications.update(email_sent_on=timezone.now())
        send_user_email_digest_sent_event(user, cadence_type, notifications_list, message_context)
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
    users = list(User.objects.filter(id__in=user_list))
    language_prefs = get_language_preference_for_users(user_list)
    course_name = get_course_info(course_key).get("name", course_key)
    for user in users:
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
        last_sent_notification = Notification.objects.filter(
            email_sent_on__isnull=False,
            email_sent_on__gte=timezone.now() - timedelta(minutes=settings.NOTIFICATION_IMMEDIATE_EMAIL_BUFFER),
            user=user
        ).order_by('-email_sent_on').first()

        if last_sent_notification:
            logger.info(f'<Immediate Email> Recent email sent to {user.username}, skipping immediate email')
            user_language = language_prefs.get(user.id, 'en')
            send_digest_email_to_user_async.apply_async(
                kwargs={
                    'user_id': user.id,
                    'cadence_type': EmailCadence.IMMEDIATELY,
                    'start_date': last_sent_notification.email_sent_on,
                    'end_date': datetime.today() + timedelta(days=1),
                    'user_language': user_language,
                },
                countdown=settings.NOTIFICATION_IMMEDIATE_EMAIL_BUFFER * 60
            )

        else:
            language = language_prefs.get(user.id, 'en')
            with translation_override(language):
                soup = BeautifulSoup(notification.content, "html.parser")
                title = _(
                    "New Course Update") if notification.notification_type == "course_updates" else soup.get_text()
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
                notification.email_sent_on = timezone.now()
                notification.save()
                send_immediate_email_digest_sent_event(user, EmailCadence.IMMEDIATELY, notification)
