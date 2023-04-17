"""
content_staging Django application initialization.
"""
from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs

from openedx.core.djangoapps.plugins.constants import ProjectType


class ContentStagingAppConfig(AppConfig):
    """
    Configuration for the content_staging Django plugin application.
    See: https://github.com/openedx/edx-platform/blob/master/openedx/core/djangoapps/plugins/README.rst
    """

    name = 'openedx.core.djangoapps.content_staging'
    verbose_name = 'Content Staging (and clipboard) API'
    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: '',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
        },
    }
