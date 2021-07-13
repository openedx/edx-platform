"""
Signal handlers for course apps.
"""
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.course_apps.models import CourseAppStatus

from openedx.core.djangoapps.course_apps.plugins import CourseAppsPluginManager
from xmodule.modulestore.django import SignalHandler

from .signals import COURSE_APP_STATUS_INIT


@receiver(SignalHandler.course_published)
def update_course_apps(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Whenever the course is published, update the status of course apps in the
    django models to match their status in the course.
    """
    course_apps = CourseAppsPluginManager.get_apps_available_for_course(course_key)
    for course_app in course_apps:
        is_enabled = course_app.is_enabled(course_key=course_key)
        CourseAppStatus.update_status_for_course_app(
            course_key=course_key,
            app_id=course_app.app_id,
            enabled=is_enabled,
        )


# pylint: disable=unused-argument
@receiver(COURSE_APP_STATUS_INIT)
def initialize_course_app_status(sender: str, course_key: CourseKey, is_enabled: bool, **kwargs):
    """
    Create a new CourseAppStatus object when a course app is accessed for the first time.

    For existing courses CourseAppStatus object might not exist. This handler creates a new
    CourseAppStatus object in such cases.

    Args:
        sender (str): The sender is the app_id for the app being accessed for the first time.
        course_key (CourseKey): The key for the course run the app is associated with
        is_enabled (bool): The status of the course app
    """
    CourseAppStatus.update_status_for_course_app(course_key=course_key, app_id=sender, enabled=is_enabled)
