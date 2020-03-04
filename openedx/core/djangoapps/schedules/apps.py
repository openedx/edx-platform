

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _

from openedx.core.djangoapps.plugins.constants import PluginSignals, ProjectType


class SchedulesConfig(AppConfig):
    name = 'openedx.core.djangoapps.schedules'
    verbose_name = _('Schedules')

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals, tasks  # pylint: disable=unused-variable
