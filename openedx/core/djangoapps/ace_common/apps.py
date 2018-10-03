"""
Configuration for the ace_common Django app.
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import ProjectType, PluginSettings, SettingsType


class AceCommonConfig(AppConfig):
    """
    Configuration class for the ace_common Django app.
    """
    name = 'openedx.core.djangoapps.ace_common'
    verbose_name = _('ACE Common')

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: u'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack'},
            },
            ProjectType.CMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: u'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack'},
            }
        }
    }
