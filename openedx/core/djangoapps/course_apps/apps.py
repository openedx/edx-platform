"""
Pluggable app config for course apps.
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class CourseAppsConfig(AppConfig):
    """
    Configuration class for Course Apps.
    """

    name = "openedx.core.djangoapps.course_apps"
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: "course_apps_api",
                PluginURLs.REGEX: r"^api/course_apps/",
                PluginURLs.RELATIVE_PATH: "rest_api.urls",
            }
        },
    }
