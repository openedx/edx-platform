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
    name = 'lms.djangoapps.lms_initialization'
    verbose_name = 'LMS Initialization'

    def ready(self):
        """
        Global LMS initialization methods are called here.  This runs after
        settings have loaded, but before most other djangoapp initializations.
        """
        self._initialize_analytics()

    def _initialize_analytics(self):
        """
        Initialize Segment analytics module by setting the write_key.
        """
        if settings.LMS_SEGMENT_KEY:
            analytics.write_key = settings.LMS_SEGMENT_KEY
