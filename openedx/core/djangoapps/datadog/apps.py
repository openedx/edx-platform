"""
Configuration for datadog Django app
"""
from django.apps import AppConfig
from django.conf import settings
from dogapi import dog_http_api, dog_stats_api


class DatadogConfig(AppConfig):
    """
    Configuration class for datadog Django app
    """
    name = 'openedx.core.djangoapps.datadog'
    verbose_name = "Datadog"

    def ready(self):
        """
        Initialize connection to datadog during django startup.

        Configure using DATADOG dictionary in the django project settings.
        """
        # By default use the statsd agent
        options = {'statsd': True}

        if hasattr(settings, 'DATADOG'):
            options.update(settings.DATADOG)

        # Not all arguments are documented.
        # Look at the source code for details.
        dog_stats_api.start(**options)

        dog_http_api.api_key = options.get('api_key')
