"""
Monitoring utilities for the LMS.
"""
import logging

from django.conf import settings
from django.utils.module_loading import import_string

log = logging.getLogger(__name__)


def get_configured_newrelic_app_name_suffix_handler():
    """
    Returns configured handler as function, imported from setting, or None if
    not configured or on import error.
    """
    if not settings.NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER:
        return None

    try:
        return import_string(settings.NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER)

    except ImportError as e:
        log.error('Could not import NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER with value %s: %s.' % (
            settings.NEWRELIC_PATH_TO_APP_NAME_SUFFIX_HANDLER, e
        ))

    return None
