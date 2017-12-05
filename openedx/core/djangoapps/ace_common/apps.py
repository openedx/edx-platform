"""
Configuration for the ace_common Django app.
"""
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class AceCommonConfig(AppConfig):
    """
    Configuration class for the ace_common Django app.
    """
    name = 'openedx.core.djangoapps.ace_common'
    verbose_name = _('ACE Common')
