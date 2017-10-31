"""
Initialization app for the LMS

This app consists solely of a ready method in its AppConfig, and should be
included early in the INSTALLED_APPS list.
"""

import analytics
from django.apps import AppConfig
from django.conf import settings


class LMSInitializationConfig(AppConfig):
    """
    Application Configuration for lms_initialization.
    """
    name = 'lms_initialization'
    verbose_name = 'LMS Initialization'

    def ready(self):
        """
        Global LMS initialization methods are called here.  This runs after
        settings have loaded, but before most other djangoapp initializations.
        """
        pass
