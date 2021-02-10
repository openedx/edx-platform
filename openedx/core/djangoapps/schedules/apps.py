# lint-amnesty, pylint: disable=missing-module-docstring

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SchedulesConfig(AppConfig):  # lint-amnesty, pylint: disable=missing-class-docstring
    name = 'openedx.core.djangoapps.schedules'
    verbose_name = _('Schedules')

    def ready(self):
        pass
