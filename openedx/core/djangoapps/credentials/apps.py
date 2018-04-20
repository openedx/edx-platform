"""
Credentials Configuration
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginSettings


class CredentialsConfig(AppConfig):
    """
    Configuration class for credentials Django app
    """
    name = 'openedx.core.djangoapps.credentials'
    verbose_name = _("Credentials")

    plugin_app = {
        PluginSettings.CONFIG: {
            ProjectType.LMS: {
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: u'settings.aws'},
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.DEVSTACK: {PluginSettings.RELATIVE_PATH: u'settings.devstack'},
                SettingsType.TEST: {PluginSettings.RELATIVE_PATH: u'settings.test'},
            }
        }
    }
