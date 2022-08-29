"""Configuration for the appsembler.eventtracking Django app."""
import os
import sys

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
        # only want to prefill the cache on lms runserver...
        is_not_lms = os.getenv("SERVICE_VARIANT") != 'lms'
        is_celery_worker = os.getenv('CELERY_WORKER_RUNNING', False)
        is_not_runserver = 'runserver' not in sys.argv
        if is_not_runserver or is_not_lms or is_celery_worker:
            return

        # ...and don't want every LMS instance calling this either, but
        # the first one to start should set PREFILLING

        metadatacache = tahoeusermetadata.userprofile_metadata_cache

        if not metadatacache.READY and not metadatacache.PREFILLING:
            tahoeusermetadata.prefetch_tahoe_usermetadata_cache.delay(metadatacache)
