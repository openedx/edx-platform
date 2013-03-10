from dogapi import dog_http_api, dog_stats_api
from django.conf import settings

if hasattr(settings, 'DATADOG_API'):
    dog_http_api.api_key = settings.DATADOG_API
    dog_stats_api.start(api_key=settings.DATADOG_API, statsd=True)
