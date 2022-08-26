"""Configuration for the appsembler.eventtracking Django app."""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import ProjectType, PluginSignals

from . import tahoeusermetadata


class EventTrackingConfig(AppConfig):
    """Configuration class for the appsembler.eventtracking Django app."""

    label = 'appsembler_eventtracking'
    name = 'openedx.core.djangoapps.appsembler.eventtracking'
    verbose_name = _('Appsembler Event Tracking')

    # TODO: signal receiver from tahoe_userprofile_metadata_cache task
    plugin_app = {
        PluginSignals.CONFIG: {
            ProjectType.LMS: {
                PluginSignals.RECEIVERS: [
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: 'invalidate_user_metadata_cache_entry',
                        PluginSignals.SIGNAL_PATH: 'django.db.models.signals.post_save',
                        PluginSignals.SENDER_PATH: 'student.models.UserProfile',
                    },
                    {
                        PluginSignals.RECEIVER_FUNC_NAME: 'invalidate_user_metadata_cache_entry',
                        PluginSignals.SIGNAL_PATH: 'django.db.models.signals.post_delete',
                        PluginSignals.SENDER_PATH: 'student.models.UserProfile',
                    }
                ]
            }
        }
    }

    def ready(self):
        metadatacache = tahoeusermetadata.userprofile_metadata_cache

        # TODO: we don't want to do this for every management command
        # TODO: we also want to make sure this is shared across worker and app instances
        if not metadatacache.READY:
            tahoeusermetadata.prefetch_tahoe_usermetadata_cache.delay(metadatacache)
