"""
This file contains celery tasks for course apps.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator

from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_apps.models import CourseAppStatus
from openedx.core.djangoapps.course_apps.plugins import CourseAppsPluginManager

log = get_task_logger(__name__)


@shared_task(name='openedx.core.djangoapps.course_apps.tasks.cache_all_course_apps_status')
@set_code_owner_attribute
def cache_all_course_apps_status():
    """
    Create CourseAppStatus entries for all course apps, across all courses to speed up queries.
    """
    course_app_plugins = CourseAppsPluginManager.get_available_plugins().values()
    log.info("Caching course apps status for all courses started")
    for course_key in CourseOverview.objects.values_list('id', flat=True):
        if isinstance(course_key, LibraryLocator):
            continue
        for plugin in course_app_plugins:
            # For current plugins this is just reading a django setting or returning a bool value
            if plugin.is_available(course_key):
                is_enabled = plugin.is_enabled(course_key)
                CourseAppStatus.objects.update_or_create(
                    course_key=course_key,
                    app_id=plugin.app_id,
                    defaults={'enabled': is_enabled}
                )
    log.info("Caching course apps status for all courses complete")


@shared_task(name='openedx.core.djangoapps.course_apps.tasks.update_course_apps_status')
@set_code_owner_attribute
def update_course_apps_status(course_key: CourseKey):
    """
    Create CourseAppStatus entries for apps available for the specified course.
    """
    course_apps = CourseAppsPluginManager.get_apps_available_for_course(course_key)
    log.info("Caching course apps status for course with id: %s", course_key)
    for course_app in course_apps:
        is_enabled = course_app.is_enabled(course_key=course_key)
        CourseAppStatus.update_status_for_course_app(
            course_key=course_key,
            app_id=course_app.app_id,
            enabled=is_enabled,
        )
