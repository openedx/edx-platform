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
    name = 'openedx.core.djangoapps.appsembler.settings'
    verbose_name = _('Appsembler Settings')

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack_lms'},
            },
            ProjectType.CMS: {
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack_cms'},
            }
        }
    }
