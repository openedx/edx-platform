"""
Django template context processors.
"""

from django.conf import settings

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def configuration_context(request):  # pylint: disable=unused-argument
    """
    Configuration context for django templates.
    """
    return {
        'google_analytics_tracking_ids': request.site.siteconfiguration.google_analytics_tracking_ids,
        'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        'segment_key': request.site.siteconfiguration.default_segment_key,
    }
