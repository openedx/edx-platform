"""
Monitoring utilities for the LMS.

Note: In order to enable rollout of new request path to NewRelic app name
    suffix mappings via config, and simple rollback, this module may
    contain multiple implementations (the current and the last).

"""
import logging
import re
from enum import Enum

from django.conf import settings
from django.utils.module_loading import import_string

log = logging.getLogger(__name__)


class AppNameSuffix(Enum):
    bom_squad = 'bom-squad'


SINGLE_REQUEST_PATH_REGEX_TO_SUFFIX_MAPPINGS = [
    # /api-admin/api/v1/api_access_request/
    (re.compile(r'^\/api-admin\/api\/v1\/api_access_request\/?$'), AppNameSuffix.bom_squad),
]


def newrelic_single_app_name_suffix_handler(request_path):
    """
    Takes a request path and returns the mapped NewRelic app name suffix if any is found.

    This implementation has a single mapping for initial rollout testing.
    """
    for path_regex, suffix in SINGLE_REQUEST_PATH_REGEX_TO_SUFFIX_MAPPINGS:
        if path_regex.search(request_path):
            return suffix.value

    return None

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
