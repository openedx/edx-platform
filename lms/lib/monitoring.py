"""
Monitoring utilities for the LMS.
"""
import logging
import time
from django.conf import settings
from django.utils.module_loading import import_string
from edx_django_utils.monitoring import set_custom_metric

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


# load and cache the mapping handler
newrelic_app_name_suffix_handler = get_configured_newrelic_app_name_suffix_handler()


def set_new_relic_app_name(environ):
    """
    Sets the NewRelic app name based on environ['PATH_INFO'].
    """
    if not newrelic_app_name_suffix_handler:
        return
    if 'PATH_INFO' not in environ:
        return
    if 'newrelic.app_name' not in environ:
        return

    try:
        before_time = time.perf_counter()
        request_path = environ.get('PATH_INFO')
        suffix = newrelic_app_name_suffix_handler(request_path)
        if suffix:
            new_app_name = "{}-{}".format(environ['newrelic.app_name'], suffix)
            environ['newrelic.app_name'] = new_app_name
            # We may remove this metric later, but for now, it can be used to confirm that
            # the updated_app_name matches the app name, and that these set_custom_metric
            # calls are making it to the appropriate transaction.
            set_custom_metric('updated_app_name', new_app_name)
        after_time = time.perf_counter()
        # Tracking the time can be used to enable alerting if this ever gets too large.
        set_custom_metric('suffix_mapping_time', round(after_time - before_time, 4))
    except Exception as e:
        set_custom_metric('suffix_mapping_error', e)
