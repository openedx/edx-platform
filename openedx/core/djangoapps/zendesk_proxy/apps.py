"""
Zendesk Proxy Configuration

"""

from django.apps import AppConfig

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginURLs, PluginSettings


class ZendeskProxyConfig(AppConfig):
    """
    AppConfig for zendesk proxy app
    """
    name = 'openedx.core.djangoapps.zendesk_proxy'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: r'^zendesk_proxy/',
                PluginURLs.RELATIVE_PATH: 'urls',
            },
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: '',
                PluginURLs.REGEX: r'^zendesk_proxy/',
                PluginURLs.RELATIVE_PATH: 'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: 'settings.aws'},
            },
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: 'settings.common'},
                SettingsType.AWS: {PluginSettings.RELATIVE_PATH: 'settings.aws'},
            }
        }
    }
