"""
Python APIs for Course Apps.
"""
from django.contrib.auth import get_user_model
from edx_django_utils.plugins import PluginError
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.course_apps.models import CourseAppStatus
from rest_framework.exceptions import ValidationError

from .plugins import CourseAppsPluginManager
from .signals import COURSE_APP_STATUS_INIT


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
    try:
        course_app_status = CourseAppStatus.objects.get(course_key=course_key, app_id=app_id)
        is_enabled = course_app_status.enabled
    except CourseAppStatus.DoesNotExist:
        course_app = CourseAppsPluginManager.get_plugin(app_id)
        is_enabled = course_app.is_enabled(course_key)
        # If the status doesn't exist it means this is an existing course so
        # dispatch an initialisation signal to make sure the next request is
        # direct from the database.
        COURSE_APP_STATUS_INIT.send(
            sender=app_id,
            course_key=course_key,
            is_enabled=is_enabled,
        )
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
    CourseAppStatus.update_status_for_course_app(
        course_key=course_key,
        app_id=app_id,
        enabled=enabled,
    )
    return enabled


def set_course_app_status(course_key: CourseKey, app_id: str, enabled: bool, user: User) -> bool:
    """
    Enable or disable a course app for a given course.

    Args:
        course_key (CourseKey): The course key for the course to update.
        app_id (str): The app ID of the course app to enable/disable.
        enabled (bool): The desired enabled status.
        user (User): The user performing the operation.

    Returns:
        bool: The final enabled/disabled status of the app.
    """
    try:
        course_app = CourseAppsPluginManager.get_plugin(app_id)
    except PluginError:
        course_app = None
    if not course_app or not course_app.is_available(course_key):
        raise ValidationError({"id": "Invalid app ID"})

    return set_course_app_enabled(course_key=course_key, app_id=app_id, enabled=enabled, user=user)
