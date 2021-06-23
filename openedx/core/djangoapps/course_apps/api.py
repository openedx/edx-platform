"""
Python APIs for Course Apps.
"""
from django.contrib.auth import get_user_model
from opaque_keys.edx.keys import CourseKey

from .plugins import CourseAppsPluginManager


User = get_user_model()


def is_course_app_enabled(course_key: CourseKey, app_id: str) -> bool:
    """
    Return if the app with the specified `app_id` is enabled for the
    specified course.

    Args:
        course_key (CourseKey): Course key for course
        app_id (str): The app id for a course app

    Returns:
        True or False depending on if the course app is enabled or not.
    """
    course_app = CourseAppsPluginManager.get_plugin(app_id)
    is_enabled = course_app.is_enabled(course_key)
    return is_enabled


def set_course_app_enabled(course_key: CourseKey, app_id: str, enabled: bool, user: User) -> bool:
    """
    Enable/disable a course app.

    Args:
        course_key (CourseKey): ID of course to operate on
        app_id (str): The app ID of the app to enabled/disable
        enabled (bool): The enable/disable status to apply
        user (User): The user performing the operation.

    Returns:
        The final enabled/disabled status of the app.
    """
    course_app = CourseAppsPluginManager.get_plugin(app_id)
    enabled = course_app.set_enabled(course_key, user=user, enabled=enabled)
    return enabled
