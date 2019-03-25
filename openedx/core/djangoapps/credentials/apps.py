"""
Credentials Configuration
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from openedx.core.djangoapps.plugins.constants import ProjectType, SettingsType, PluginSettings, PluginSignals


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
        },
        PluginSignals.CONFIG: {
            ProjectType.LMS: {
                PluginSignals.RECEIVERS: [
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: u'handle_grade_change',
                        PluginSignals.SIGNAL_PATH: u'openedx.core.djangoapps.signals.signals.COURSE_GRADE_CHANGED',
                    },
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: u'handle_cert_change',
                        PluginSignals.SIGNAL_PATH: u'openedx.core.djangoapps.signals.signals.COURSE_CERT_CHANGED',
                    },
                ],
            },
        },
    }

    def ready(self):
        # Register celery workers
        from .tasks.v1 import tasks  # pylint: disable=unused-variable
