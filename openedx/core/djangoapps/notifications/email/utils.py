"""
Email Notifications Utils
"""
import datetime
import json
import logging

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from pytz import utc
from waffle import get_waffle_flag_model   # pylint: disable=invalid-django-waffle-import

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.branding.api import get_logo_url_for_email
from lms.djangoapps.discussion.notification_prefs.views import UsernameCipher
from openedx.core.djangoapps.notifications.base_notification import (
    COURSE_NOTIFICATION_APPS,
    COURSE_NOTIFICATION_TYPES,
)
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_EMAIL_NOTIFICATIONS
from openedx.core.djangoapps.notifications.email_notifications import EmailCadence
from openedx.core.djangoapps.notifications.events import notification_preference_unsubscribe_event
from openedx.core.djangoapps.notifications.models import (
    CourseNotificationPreference,
    get_course_notification_preference_config_version
)
from xmodule.modulestore.django import modulestore

from .notification_icons import NotificationTypeIcons


User = get_user_model()
log = logging.getLogger(__name__)


def is_email_notification_flag_enabled(user=None):
    """
    Returns if waffle flag is enabled for user or not
    """
    flag_model = get_waffle_flag_model()
    try:
        flag = flag_model.objects.get(name=ENABLE_EMAIL_NOTIFICATIONS.name)
    except flag_model.DoesNotExist:
        return False
    if flag.everyone is not None:
        return flag.everyone
    if user:
        role_value = flag.is_active_for_user(user)
        if role_value is not None:
            return role_value
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


def get_unsubscribe_link(username, patch):
    """
    Returns unsubscribe url for username with patch preferences
    """
    encrypted_username = encrypt_string(username)
    encrypted_patch = encrypt_object(patch)
    return f"{settings.LEARNING_MICROFRONTEND_URL}/preferences-unsubscribe/{encrypted_username}/{encrypted_patch}"


def create_email_template_context(username):
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
    patch = {
        'channel': 'email',
        'value': False
    }
    return {
        "platform_name": settings.PLATFORM_NAME,
        "mailing_address": settings.CONTACT_MAILING_ADDRESS,
        "logo_url": get_logo_url_for_email(),
        "social_media": social_media_info,
        "notification_settings_url": f"{settings.ACCOUNT_MICROFRONTEND_URL}/notifications",
        "unsubscribe_url": get_unsubscribe_link(username, patch)
    }


def create_email_digest_context(app_notifications_dict, username, start_date, end_date=None, digest_frequency="Daily",
                                courses_data=None):
    """
    Creates email context based on content
    app_notifications_dict: Mapping of notification app and its count, title and notifications
    start_date: datetime instance
    end_date: datetime instance
    digest_frequency: EmailCadence.DAILY or EmailCadence.WEEKLY
    courses_data: Dictionary to cache course info (avoid additional db calls)
    """
    context = create_email_template_context(username)
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


def add_headers_to_email_message(message, context):
    """
    Add headers to email message
    """
    if context.get('unsubscribe_url'):
        message.headers['List-Unsubscribe-Post'] = f"<{context['unsubscribe_url']}>"
        message.headers['List-Unsubscribe'] = f"<{context['unsubscribe_url']}>"
    return message


def get_start_end_date(cadence_type):
    """
    Returns start_date and end_date for email digest
    """
    if cadence_type not in [EmailCadence.DAILY, EmailCadence.WEEKLY]:
        raise ValueError('Invalid cadence_type')
    end_date = datetime.datetime.now()
    start_date = end_date - datetime.timedelta(days=1, minutes=15)
    if cadence_type == EmailCadence.WEEKLY:
        start_date = start_date - datetime.timedelta(days=6)
    return utc.localize(start_date), utc.localize(end_date)


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
    current_date = utc.localize(datetime.datetime.today())
    days_diff = (current_date - datetime_obj).days
    if days_diff == 0:
        return "Today"
    if days_diff >= 7:
        return f"{int(days_diff / 7)}w"
    return f"{days_diff}d"


def add_zero_margin_to_root(html_string):
    """
    Adds to zero margin to root element of html string
    """
    soup = BeautifulSoup(html_string, 'html.parser')
    element = soup.find()
    if not element:
        return html_string
    element['style'] = "margin: 0;"
    return str(soup)


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
        notification.email_content = add_zero_margin_to_root(notification.content)
        notification.details = add_zero_margin_to_root(notification.content_context.get('email_content', ''))
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


def get_unique_course_ids(notifications):
    """
    Returns unique course_ids from notifications
    """
    course_ids = []
    for notification in notifications:
        if notification.course_id not in course_ids:
            course_ids.append(notification.course_id)
    return course_ids


def get_enabled_notification_types_for_cadence(preferences, cadence_type=EmailCadence.DAILY):
    """
    Returns a dictionary that returns notification_types with cadence_types for course_ids
    """
    if cadence_type not in [EmailCadence.DAILY, EmailCadence.WEEKLY]:
        raise ValueError('Invalid cadence_type')
    course_types = {}
    for preference in preferences:
        key = preference.course_id
        value = []
        config = preference.notification_preference_config
        for app_data in config.values():
            for notification_type, type_dict in app_data['notification_types'].items():
                if (type_dict['email_cadence'] == cadence_type) and type_dict['email']:
                    value.append(notification_type)
            if 'core' in value:
                value.remove('core')
                value.extend(app_data['core_notification_types'])
        course_types[key] = value
    return course_types


def filter_notification_with_email_enabled_preferences(notifications, preferences, cadence_type=EmailCadence.DAILY):
    """
    Filter notifications for types with email cadence preference enabled
    """
    enabled_course_prefs = get_enabled_notification_types_for_cadence(preferences, cadence_type)
    filtered_notifications = []
    for notification in notifications:
        if notification.notification_type in enabled_course_prefs[notification.course_id]:
            filtered_notifications.append(notification)
    return filtered_notifications


def encrypt_string(string):
    """
    Encrypts input string
    """
    return UsernameCipher.encrypt(string)


def decrypt_string(string):
    """
    Decrypts input string
    """
    return UsernameCipher.decrypt(string).decode()


def encrypt_object(obj):
    """
    Returns hashed string of object
    """
    string = json.dumps(obj)
    return encrypt_string(string)


def decrypt_object(string):
    """
    Decrypts input string and returns an object
    """
    decoded = decrypt_string(string)
    return json.loads(decoded)


def update_user_preferences_from_patch(encrypted_username, encrypted_patch):
    """
    Decrypt username and patch and updates user preferences
    Allowed parameters for decrypted patch
        app_name: name of app
        notification_type: notification type name
        channel: channel name ('web', 'push', 'email')
        value: True or False
        course_id: course key string
    """
    username = decrypt_string(encrypted_username)
    patch = decrypt_object(encrypted_patch)

    app_value = patch.get("app_name")
    type_value = patch.get("notification_type")
    channel_value = patch.get("channel")
    pref_value = bool(patch.get("value", False))
    user = get_object_or_404(User, username=username)

    kwargs = {'user': user}
    if 'course_id' in patch.keys():
        kwargs['course_id'] = patch['course_id']

    def is_name_match(name, param_name):
        """
        Name is match if strings are equal or param_name is None
        """
        return True if param_name is None else name == param_name

    def is_editable(app_name, notification_type, channel):
        """
        Returns if notification type channel is editable
        """
        if notification_type == 'core':
            return channel not in COURSE_NOTIFICATION_APPS[app_name]['non_editable']
        return channel not in COURSE_NOTIFICATION_TYPES[notification_type]['non_editable']

    def get_default_cadence_value(app_name, notification_type):
        """
        Returns default email cadence value
        """
        if notification_type == 'core':
            return COURSE_NOTIFICATION_APPS[app_name]['core_email_cadence']
        return COURSE_NOTIFICATION_TYPES[notification_type]['email_cadence']

    def get_updated_preference(pref):
        """
        Update preference if config version doesn't match
        """
        if pref.config_version != get_course_notification_preference_config_version():
            pref = pref.get_user_course_preference(pref.user_id, pref.course_id)
        return pref

    course_ids = CourseEnrollment.objects.filter(user=user).values_list('course_id', flat=True)
    CourseNotificationPreference.objects.bulk_create(
        [
            CourseNotificationPreference(user=user, course_id=course_id)
            for course_id in course_ids
        ],
        ignore_conflicts=True
    )
    preferences = CourseNotificationPreference.objects.filter(**kwargs)

    # pylint: disable=too-many-nested-blocks
    for preference in preferences:
        preference = get_updated_preference(preference)
        preference_json = preference.notification_preference_config
        for app_name, app_prefs in preference_json.items():
            if not is_name_match(app_name, app_value):
                continue
            for noti_type, type_prefs in app_prefs['notification_types'].items():
                if not is_name_match(noti_type, type_value):
                    continue
                for channel in ['web', 'email', 'push']:
                    if not is_name_match(channel, channel_value):
                        continue
                    if is_editable(app_name, noti_type, channel):
                        type_prefs[channel] = pref_value
                        if channel == 'email':
                            cadence_value = get_default_cadence_value(app_name, noti_type)\
                                if pref_value else EmailCadence.NEVER
                            type_prefs['email_cadence'] = cadence_value
        preference.save()
    if not user.id:
        log.info(f"<Digest-One-Click-Unsubscribe> - user.id is null - {encrypted_username} ")
    notification_preference_unsubscribe_event(user)
