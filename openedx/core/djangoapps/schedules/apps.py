from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class SchedulesConfig(AppConfig):
    name = 'openedx.core.djangoapps.schedules'
    verbose_name = _('Schedules')

    def ready(self):
        # noinspection PyUnresolvedReferences
        from . import signals  # pylint: disable=unused-variable
