from __future__ import absolute_import

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import PluginSignals, ProjectType


class SchedulesConfig(AppConfig):
    name = 'openedx.core.djangoapps.schedules'
    verbose_name = _('Schedules')

    plugin_app = {
        PluginSignals.CONFIG: {
            ProjectType.LMS: {
                PluginSignals.RECEIVERS: [{
                    PluginSignals.RECEIVER_FUNC_NAME: u'update_schedules_on_course_start_changed',
                    PluginSignals.SIGNAL_PATH: u'openedx.core.djangoapps.content.course_overviews.signals.COURSE_START_DATE_CHANGED',  # pylint: disable=line-too-long
                }]
            },
            ProjectType.CMS: {
                PluginSignals.RECEIVERS: [{
                    PluginSignals.RECEIVER_FUNC_NAME: u'update_schedules_on_course_start_changed',
                    PluginSignals.SIGNAL_PATH: u'openedx.core.djangoapps.content.course_overviews.signals.COURSE_START_DATE_CHANGED',  # pylint: disable=line-too-long
                }]
            },
        },
    }

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals, tasks  # pylint: disable=unused-variable
