"""
Configuration for the ace_common Django app.
"""


from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _
from edx_django_utils.plugins import PluginSettings

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class AceCommonConfig(AppConfig):
    """
    Configuration class for the ace_common Django app.
    """
    name = 'openedx.core.djangoapps.ace_common'
    verbose_name = _('ACE Common')

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: 'settings.devstack'},
            },
            ProjectType.CMS: {
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: 'settings.production'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: 'settings.devstack'},
            }
        }
    }
