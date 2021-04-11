

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _
from edx_django_utils.plugins import PluginSignals

from openedx.core.djangoapps.plugins.constants import ProjectType


class SchedulesConfig(AppConfig):
    name = 'openedx.core.djangoapps.schedules'
    verbose_name = _('Schedules')

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals, tasks  # pylint: disable=unused-variable
