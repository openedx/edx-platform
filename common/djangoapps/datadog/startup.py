from django.conf import settings

from dogapi import dog_stats_api, dog_http_api


def run():
    """
    Initialize connection to datadog during django startup.

    Can be configured using a dictionary named DATADOG in the django
    project settings.

    """

    # By default use the statsd agent
    options = {'statsd': True}

    if hasattr(settings, 'DATADOG'):
        options.update(settings.DATADOG)

    # Not all arguments are documented.
    # Look at the source code for details.
    dog_stats_api.start(**options)

    dog_http_api.api_key = options.get('api_key')
