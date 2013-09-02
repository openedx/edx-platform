from django.conf import settings
from dogapi import dog_http_api, dog_stats_api

def run():
    """
    Initialize connection to datadog during django startup.

    Expects the datadog api key in the DATADOG_API settings key
    """
    if hasattr(settings, 'DATADOG_API'):
        dog_http_api.api_key = settings.DATADOG_API
        dog_stats_api.start(api_key=settings.DATADOG_API, statsd=True)
