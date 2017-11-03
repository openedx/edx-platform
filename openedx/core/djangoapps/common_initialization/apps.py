"""
Common initialization app for the LMS and CMS
"""

from django.apps import AppConfig


class CommonInitializationConfig(AppConfig):
    name = 'openedx.core.djangoapps.common_initialization'
    verbose_name = 'Common Initialization'

    def ready(self):
        # Common settings validations for the LMS and CMS.
        from . import checks
