"""
Zendesk Proxy Configuration

"""


from django.apps import AppConfig
from edx_django_utils.plugins import PluginURLs, PluginSettings

from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType


class ZendeskProxyConfig(AppConfig):
    """
    AppConfig for zendesk proxy app
    """
    name = 'openedx.core.djangoapps.zendesk_proxy'

    plugin_app = {
        PluginURLs.CONFIG: {
            ProjectType.CMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: r'^zendesk_proxy/',
                PluginURLs.RELATIVE_PATH: u'urls',
            },
            ProjectType.LMS: {
                PluginURLs.NAMESPACE: u'',
                PluginURLs.REGEX: r'^zendesk_proxy/',
                PluginURLs.RELATIVE_PATH: u'urls',
            }
        },
        PluginSettings.CONFIG: {
            ProjectType.CMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production'},
            },
            ProjectType.LMS: {
                SettingsType.COMMON: {PluginSettings.RELATIVE_PATH: u'settings.common'},
                SettingsType.PRODUCTION: {PluginSettings.RELATIVE_PATH: u'settings.production'},
            }
        }
    }
