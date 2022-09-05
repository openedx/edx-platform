"""Configuration for the appsembler.eventtracking Django app."""

import logging

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import ProjectType, PluginSignals
from track.shim import is_celery_worker

from . import app_variant, tahoeusermetadata


logger = logging.getLogger(__name__)


class EventTrackingConfig(AppConfig):
    """Configuration class for the appsembler.eventtracking Django app."""

    label = 'appsembler_eventtracking'
    name = 'openedx.core.djangoapps.appsembler.eventtracking'
    verbose_name = _('Appsembler Event Tracking')

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
            },
            ProjectType.CMS: {
                PluginSignals.RECEIVERS: [
                    # just to invalidate cache if UserProfile changed, maybe in Django admin
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
        metadatacache.ready()

        # only want to prefill the cache on lms runserver...
        if (
            app_variant.is_not_runserver() or
            app_variant.is_not_lms() or
            is_celery_worker()
        ):
            logger.debug("Not initializing metadatacache. This is Studio, Celery, other command.")
            return
        else:
            tahoeusermetadata.prefetch_tahoe_usermetadata_cache.delay(metadatacache)
