"""
Django template context processors.
"""


from django.conf import settings
from django.utils.http import urlquote_plus

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers


def configuration_context(request):
    """
    Configuration context for django templates.
    """
    return {
        'platform_name': configuration_helpers.get_value('platform_name', settings.PLATFORM_NAME),
        'current_url': urlquote_plus(request.build_absolute_uri(request.path)),
        'current_site_url': urlquote_plus(request.build_absolute_uri('/')),
        'settings': settings,
        'zendesk_widget': settings.MKTG_URLS.get('ZENDESK-WIDGET'),
    }
