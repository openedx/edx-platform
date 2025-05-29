"""
Utils function for notifications app
"""
import copy
from typing import Dict, List, Set

from common.djangoapps.student.models import CourseAccessRole, CourseEnrollment
from openedx.core.djangoapps.django_comment_common.models import Role
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.lib.cache_utils import request_cached


def find_app_in_normalized_apps(app_name, apps_list):
    """
    Returns app preference based on app_name
    """
    for app in apps_list:
        if app.get('name') == app_name:
            return app
    return None


def find_pref_in_normalized_prefs(pref_name, app_name, prefs_list):
    """
    Returns preference based on preference_name and app_name
    """
    for pref in prefs_list:
        if pref.get('name') == pref_name and pref.get('app_name') == app_name:
            return pref
    return None


def get_show_notifications_tray(user):
    """
    Returns show_notifications_tray as boolean for the courses in which user is enrolled
    """
    show_notifications_tray = False
    learner_enrollments_course_ids = CourseEnrollment.objects.filter(
        user=user,
        is_active=True
    ).values_list('course_id', flat=True)

    for course_id in learner_enrollments_course_ids:
        if ENABLE_NOTIFICATIONS.is_enabled(course_id):
            show_notifications_tray = True
            break

    return show_notifications_tray


def get_list_in_batches(input_list, batch_size):
    """
    Divides the list of objects into list of list of objects each of length batch_size.
    """
    list_length = len(input_list)
    for index in range(0, list_length, batch_size):
        yield input_list[index: index + batch_size]


def get_user_forum_roles(user_id: int, course_id: str) -> List[str]:
    """
    Get forum roles for the given user in the specified course.

    :param user_id: User ID
    :param course_id: Course ID
    :return: List of forum roles
    """
    return list(Role.objects.filter(course_id=course_id, users__id=user_id).values_list('name', flat=True))


@request_cached()
def get_notification_types_with_visibility_settings() -> Dict[str, List[str]]:
    """
    Get notification types with their visibility settings.

    :return: List of dictionaries with notification type names and corresponding visibility settings
    """
    from .base_notification import COURSE_NOTIFICATION_TYPES

    notification_types_with_visibility_settings = {}
    for notification_type in COURSE_NOTIFICATION_TYPES.values():
        if notification_type.get('visible_to'):
            notification_types_with_visibility_settings[notification_type['name']] = notification_type['visible_to']

    return notification_types_with_visibility_settings


def filter_out_visible_notifications(
    user_preferences: dict,
    notifications_with_visibility: Dict[str, List[str]],
    user_forum_roles: List[str],
    user_course_roles: List[str]
) -> dict:
    """
    Filter out notifications visible to forum roles from user preferences.

    :param user_preferences: User preferences dictionary
    :param notifications_with_visibility: List of dictionaries with notification type names and
    corresponding visibility settings
    :param user_forum_roles: List of forum roles for the user
    :param user_course_roles: List of course roles for the user
    :return: Updated user preferences dictionary
    """
    for user_preferences_app, app_config in user_preferences.items():
        if 'notification_types' in app_config:
            # Iterate over the types to remove and pop them from the dictionary
            for notification_type, is_visible_to in notifications_with_visibility.items():
                is_visible = False
                for role in is_visible_to:
                    if role in user_forum_roles or role in user_course_roles:
                        is_visible = True
                        break
                if is_visible:
                    continue
                if notification_type in user_preferences[user_preferences_app]['notification_types']:
                    user_preferences[user_preferences_app]['notification_types'].pop(notification_type)
    return user_preferences


def remove_preferences_with_no_access(preferences: dict, user) -> dict:
    """
    Filter out notifications visible to forum roles from user preferences.

    :param preferences: User preferences dictionary
    :param user: User object
    :return: Updated user preferences dictionary
    """
    user_preferences = preferences['notification_preference_config']
    user_forum_roles = get_user_forum_roles(user.id, preferences['course_id'])
    notifications_with_visibility_settings = get_notification_types_with_visibility_settings()
    user_course_roles = CourseAccessRole.objects.filter(
        user=user,
        course_id=preferences['course_id']
    ).values_list('role', flat=True)
    preferences['notification_preference_config'] = filter_out_visible_notifications(
        user_preferences,
        notifications_with_visibility_settings,
        user_forum_roles,
        user_course_roles
    )
    return preferences


def clean_arguments(kwargs):
    """
    Returns query arguments from command line arguments
    """
    clean_kwargs = {}
    for key in ['app_name', 'notification_type', 'course_id']:
        if kwargs.get(key):
            clean_kwargs[key] = kwargs[key]
    if kwargs.get('created', {}):
        clean_kwargs.update(kwargs.get('created'))
    return clean_kwargs


def update_notification_types(
    app_config: Dict,
    user_app_config: Dict,
) -> None:
    """
    Update notification types for a specific category configuration.
    """
    if "notification_types" not in user_app_config:
        return

    for type_key, type_config in user_app_config["notification_types"].items():
        if type_key not in app_config["notification_types"]:
            continue

        update_notification_fields(
            app_config["notification_types"][type_key],
            type_config,
        )


def update_notification_fields(
    target_config: Dict,
    source_config: Dict,
) -> None:
    """
    Update individual notification fields (web, push, email) and email_cadence.
    """
    for field in ["web", "push", "email"]:
        if field in source_config:
            target_config[field] |= source_config[field]
    if "email_cadence" in source_config:
        if not target_config.get("email_cadence") or isinstance(target_config.get("email_cadence"), str):
            target_config["email_cadence"] = set()

        target_config["email_cadence"].add(source_config["email_cadence"])


def update_core_notification_types(app_config: Dict, user_config: Dict) -> None:
    """
    Update core notification types by merging existing and new types.
    """
    if "core_notification_types" not in user_config:
        return

    existing_types: Set = set(app_config.get("core_notification_types", []))
    existing_types.update(user_config["core_notification_types"])
    app_config["core_notification_types"] = list(existing_types)


def process_app_config(
    app_config: Dict,
    user_config: Dict,
    app: str,
    default_config: Dict,
) -> None:
    """
    Process a single category configuration against another config.
    """
    if app not in user_config:
        return

    user_app_config = user_config[app]

    # Update enabled status
    app_config["enabled"] |= user_app_config.get("enabled", False)

    # Update core notification types
    update_core_notification_types(app_config, user_app_config)

    # Update notification types
    update_notification_types(app_config, user_app_config)


def aggregate_notification_configs(existing_user_configs: List[Dict]) -> Dict:
    """
    Update default notification config with values from other configs.
    Rules:
    1. Start with default config as base
    2. If any value is True in other configs, make it True
    3. Set email_cadence to "Mixed" if different cadences found, else use default

    Args:
        existing_user_configs: List of notification config dictionaries to apply

    Returns:
        Updated config following the same structure
    """
    if not existing_user_configs:
        return {}

    result_config = copy.deepcopy(existing_user_configs[0])
    apps = result_config.keys()

    for app in apps:
        app_config = result_config[app]

        for user_config in existing_user_configs:
            process_app_config(app_config, user_config, app, existing_user_configs[0])

    # if email_cadence is mixed, set it to "Mixed"
    for app in result_config:
        for type_key, type_config in result_config[app]["notification_types"].items():
            if len(type_config.get("email_cadence", [])) > 1:
                result_config[app]["notification_types"][type_key]["email_cadence"] = "Mixed"
            else:
                result_config[app]["notification_types"][type_key]["email_cadence"] = (
                    result_config[app]["notification_types"][type_key]["email_cadence"].pop())
    return result_config


def filter_out_visible_preferences_by_course_ids(user, preferences: Dict, course_ids: List) -> Dict:
    """
    Filter out notifications visible to forum roles from user preferences.
    """
    forum_roles = Role.objects.filter(users__id=user.id).values_list('name', flat=True)
    course_roles = CourseAccessRole.objects.filter(
        user=user,
        course_id__in=course_ids
    ).values_list('role', flat=True)
    notification_types_with_visibility = get_notification_types_with_visibility_settings()
    return filter_out_visible_notifications(
        preferences,
        notification_types_with_visibility,
        forum_roles,
        course_roles
    )
