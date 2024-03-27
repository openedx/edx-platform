"""
Email Notifications Utils
"""
import datetime

from django.conf import settings
from waffle import get_waffle_flag_model   # pylint: disable=invalid-django-waffle-import

from lms.djangoapps.branding.api import get_logo_url_for_email
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_EMAIL_NOTIFICATIONS
from xmodule.modulestore.django import modulestore

from .notification_icons import NotificationTypeIcons


def is_email_notification_flag_enabled(user=None):
    """
    Returns if waffle flag is enabled for user or not
    """
    waffle_model = get_waffle_flag_model()
    flag = waffle_model.get(ENABLE_EMAIL_NOTIFICATIONS.name)
    if flag.everyone is not None:
        return flag.everyone
    role_value = flag.is_active_for_user(user)
    if role_value is not None:
        return role_value
    if user:
        try:
            return flag.users.contains(user)
        except ValueError:
            pass
    return False


def create_datetime_string(datetime_instance):
    """
    Returns string for datetime object
    """
    return datetime_instance.strftime('%A, %b %d')


def get_icon_url_for_notification_type(notification_type):
    """
    Returns icon url for notification type
    """
    return NotificationTypeIcons.get_icon_url_for_notification_type(notification_type)


def create_email_template_context():
    """
    Creates email context for header and footer
    """
    social_media_urls = settings.SOCIAL_MEDIA_FOOTER_ACE_URLS
    social_media_icons = settings.SOCIAL_MEDIA_LOGO_URLS
    social_media_info = {
        social_platform: {
            'url': social_media_urls[social_platform],
            'icon': social_media_icons[social_platform]
        }
        for social_platform in social_media_urls.keys()
        if social_media_icons.get(social_platform)
    }
    return {
        "platform_name": settings.PLATFORM_NAME,
        "mailing_address": settings.CONTACT_MAILING_ADDRESS,
        "logo_url": get_logo_url_for_email(),
        "social_media": social_media_info,
        "notification_settings_url": f"{settings.ACCOUNT_MICROFRONTEND_URL}/notifications",
    }


def create_email_digest_context(app_notifications_dict, start_date, end_date=None, digest_frequency="Daily",
                                courses_data=None):
    """
    Creates email context based on content
    app_notifications_dict: Mapping of notification app and its count, title and notifications
    start_date: datetime instance
    end_date: datetime instance
    digest_frequency: "Daily" or "Weekly"
    courses_data: Dictionary to cache course info (avoid additional db calls)
    """
    context = create_email_template_context()
    start_date_str = create_datetime_string(start_date)
    end_date_str = create_datetime_string(end_date if end_date else start_date)
    email_digest_updates = [{
        'title': 'Total Notifications',
        'count': sum(value['count'] for value in app_notifications_dict.values())
    }]
    email_digest_updates.extend([
        {
            'title': value['title'],
            'count': value['count'],
        }
        for key, value in app_notifications_dict.items()
    ])
    email_content = [
        {
            'title': value['title'],
            'help_text': value.get('help_text', ''),
            'help_text_url': value.get('help_text_url', ''),
            'notifications': add_additional_attributes_to_notifications(
                value.get('notifications', []), courses_data=courses_data
            )
        }
        for key, value in app_notifications_dict.items()
    ]
    context.update({
        "start_date": start_date_str,
        "end_date": end_date_str,
        "digest_frequency": digest_frequency,
        "email_digest_updates": email_digest_updates,
        "email_content": email_content,
    })
    return context


def get_start_end_date(cadence_type):
    """
    Returns start_date and end_date for email digest
    """
    if cadence_type not in ["Daily", "Weekly"]:
        raise ValueError('Invalid cadence_type')
    date_today = datetime.datetime.now()
    yesterday = date_today - datetime.timedelta(days=1)
    end_date = datetime.datetime.combine(yesterday, datetime.time.max)
    start_date = end_date
    if cadence_type == "Weekly":
        start_date = end_date - datetime.timedelta(days=6)
    start_date = datetime.datetime.combine(start_date, datetime.time.min)
    return start_date, end_date


def get_course_info(course_key):
    """
    Returns course info for course_key
    """
    store = modulestore()
    course = store.get_course(course_key)
    return {'name': course.display_name}


def get_time_ago(datetime_obj):
    """
    Returns time_ago for datetime instance
    """
    current_date = datetime.date.today()
    days_diff = current_date.day - datetime_obj.day
    if days_diff == 0:
        return "Today"
    if days_diff >= 7:
        return f"{int(days_diff / 7)}w"
    return f"{days_diff}d"


def add_additional_attributes_to_notifications(notifications, courses_data=None):
    """
    Add attributes required for email content to notification instance
    notifications: list[Notification]
    course_data: Cache course info
    """
    if courses_data is None:
        courses_data = {}

    for notification in notifications:
        notification_type = notification.notification_type
        course_key = notification.course_id
        course_key_str = str(course_key)
        if course_key_str not in courses_data.keys():
            courses_data[course_key_str] = get_course_info(course_key)
        course_info = courses_data[course_key_str]
        notification.course_name = course_info.get('name', '')
        notification.icon = get_icon_url_for_notification_type(notification_type)
        notification.time_ago = get_time_ago(notification.created)
    return notifications


def create_app_notifications_dict(notifications):
    """
    Return a dictionary with notification app as key and
    title, count and notifications as its value
    """
    app_names = list({notification.app_name for notification in notifications})
    app_notifications = {
        name: {
            'count': 0,
            'title': name.title(),
            'notifications': []
        }
        for name in app_names
    }
    for notification in notifications:
        app_data = app_notifications[notification.app_name]
        app_data['count'] += 1
        app_data['notifications'].append(notification)
    return app_notifications
