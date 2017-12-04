from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AceCommonConfig(AppConfig):
    name = 'openedx.core.djangoapps.ace_common'
    verbose_name = _('ACE Common')
