"""
Configuration for the appsembler.settings Django app.
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import ProjectType, PluginSettings, SettingsType


class SettingsConfig(AppConfig):
    """
    Configuration class for the appsembler.settings Django app.
    """
    label = 'appsembler_settings'
    name = 'openedx.core.djangoapps.appsembler.settings'
    verbose_name = _('Appsembler Settings')

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production_lms'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack_lms'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: u'settings.test_common'},
            },
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production_cms'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack_cms'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: u'settings.test_common'},
            }
        }
    }
