""" Utility functions related to HTTP requests """

import logging
import re
from urllib.parse import urlparse

import crum
from django.conf import settings
from django.test.client import RequestFactory
from edx_django_utils.cache import RequestCache
from edx_django_utils.monitoring import set_custom_attribute
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import exception_handler

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# accommodates course api urls, excluding any course api routes that do not fall under v*/courses, such as v1/blocks.
COURSE_REGEX = re.compile(fr'^(.*?/course(s)?/)(?!v[0-9]+/[^/]+){settings.COURSE_ID_PATTERN}')

log = logging.getLogger(__name__)


def get_request_or_stub():
    """
    Return the current request or a stub request.

    If called outside the context of a request, construct a fake
    request that can be used to build an absolute URI.

    This is useful in cases where we need to pass in a request object
    but don't have an active request (for example, in tests, celery tasks, and XBlocks).
    """
    request = crum.get_current_request()

    if request is None:

        # The settings SITE_NAME may contain a port number, so we need to
        # parse the full URL.
        full_url = f"http://{settings.SITE_NAME}"
        parsed_url = urlparse(full_url)

        # Construct the fake request.  This can be used to construct absolute
        # URIs to other paths.
        return RequestFactory(
            SERVER_NAME=parsed_url.hostname,
            SERVER_PORT=parsed_url.port or 80,
        ).get("/")

    else:
        return request


def safe_get_host(request):
    """
    Get the host name for this request, as safely as possible.

    If ALLOWED_HOSTS is properly set, this calls request.get_host;
    otherwise, this returns whatever settings.SITE_NAME is set to.

    This ensures we will never accept an untrusted value of get_host()
    """
    if isinstance(settings.ALLOWED_HOSTS, (list, tuple)) and '*' not in settings.ALLOWED_HOSTS:
        return request.get_host()
    else:
        return configuration_helpers.get_value('site_domain', settings.SITE_NAME)


def course_id_from_url(url):
    """
    Extracts the course_id from the given `url`.
    """
    if not url:
        return None

    match = COURSE_REGEX.match(url)

    if match is None:
        return None

    course_id = match.group('course_id')

    if course_id is None:
        return None

    try:
        return CourseKey.from_string(course_id)
    except InvalidKeyError:
        return None


def expected_error_exception_handler(exc, context):
    """
    Replacement for DRF's default exception handler to enable observing expected errors.

    In addition to the default behaviour, add logging and monitoring for expected errors.
    """
    # Call REST framework's default exception handler first to get the standard error response.
    response = exception_handler(exc, context)

    try:
        request = context['request'] if 'request' in context else None
    except TypeError:  # when context is not iterable
        request = None

    _log_and_monitor_expected_errors(request, exc, 'drf')
    return response


class ExpectedErrorMiddleware:
    """
    Middleware to add logging and monitoring for expected errors.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """
        Add logging and monitoring of expected errors.
        """
        _log_and_monitor_expected_errors(request, exception, 'middleware')


# .. setting_name: EXPECTED_ERRORS
# .. setting_default: None
# .. setting_description: Used to configure logging and monitoring for expected errors.
#     This setting is configured of a list of dicts. See setting and toggle annotations for
#     ``EXPECTED_ERRORS[N]['XXX']`` for details of each item in the dict.
#     If this setting is a non-empty list, all uncaught errors processed will get a ``checked_error_expected_from``
#     attribute, whether they are expected or not. Those errors that are processed and match a 'MODULE_AND_CLASS'
#     (documented elsewhere), will get an ``error_expected`` custom attribute. Unexpected errors would be errors with
#     ``error_expected IS NULL``. For additional diagnostic information for ignored errors, see the
#     EXPECTED_ERRORS[N]['IS_IGNORED'] annotation.
# .. setting_warning: We use Django Middleware and a DRF custom error handler to find uncaught errors. Some errors may
#     slip through the cracks, like ValidationError. Any error where ``checked_error_expected_from IS NULL`` is
#     an error that was not processed.

# .. setting_name: EXPECTED_ERRORS[N]['MODULE_AND_CLASS']
# .. setting_default: None
# .. setting_description: Required error module and class name that is expected. For example,
#     ``rest_framework.exceptions.PermissionDenied``.

# .. toggle_name: EXPECTED_ERRORS[N]['IS_IGNORED']
# .. toggle_implementation: DjangoSetting
# .. toggle_default: True
# .. toggle_description: Set this to False if the errors are not ignored by monitoring, but only expected, like
#      for temporary problems that may take some time to fix. If True, adds the custom attributes
#      ``error_ignored_class`` and ``error_ignored_message`` to help diagnose issues with ignored errors, since
#      this data is not otherwise available. For example of ignoring errors in New Relic, see:
#      https://docs.newrelic.com/docs/agents/manage-apm-agents/agent-data/manage-errors-apm-collect-ignore-or-mark-expected/#ignore  pylint: disable=line-too-long,useless-suppression
#      To query for ignored errors, you would use ``error_ignored_class IS NOT NULL``.
#      Note: This is defaulted to True because it will be easier for us to detect if True is not the correct value, by
#      seeing that these errors aren't actually ignored.
# .. toggle_warning: At this time, this toggle does not actually configure the error to be ignored. It is meant to match
#     the ignored error configuration found elsewhere. When monitoring, no errors should ever have the attribute
#     ``error_ignored_class``. Only Transactions should have this custom attribute. If found for an error, it means we
#     are stating an error should be ignored when it is not actually configured as such, or the configuration is not
#     working.
# .. toggle_use_cases: opt_out
# .. toggle_creation_date: 2021-03-11

# .. toggle_name: EXPECTED_ERRORS[N]['LOG_ERROR']
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: If True, the error will be logged with a message like: "Expected error ...".
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2021-03-11

# .. toggle_name: EXPECTED_ERRORS[N]['LOG_STACK_TRACE']
# .. toggle_implementation: DjangoSetting
# .. toggle_default: False
# .. toggle_description: If True, the stacktrace will be included with the logging message.
# .. toggle_warning: Requires ``LOG_ERROR`` to be set to True, otherwise this value will be ignored.
# .. toggle_use_cases: opt_in
# .. toggle_creation_date: 2021-03-11

# .. setting_name: EXPECTED_ERRORS[N]['REASON_EXPECTED']
# .. setting_default: None
# .. setting_description: Required string explaining why the error is expected and/or ignored for documentation
#     purposes.


# Warning: do not access this directly, but instead use _get_expected_error_settings_dict.
# EXPECTED ERRORS Django setting is processed and stored as a dict keyed by ERROR_MODULE_AND_CLASS.
_EXPECTED_ERROR_SETTINGS_DICT = None


def _get_expected_error_settings_dict():
    """
    Returns a dict of dicts of expected error settings used for logging and monitoring.

    The contents of the EXPECTED_ERRORS Django Setting list is processed for efficient lookup by module.Class.

    Returns:
         (dict): dict of dicts, mapping module-and-class name to settings for proper handling of expected errors.
           Keys of the inner dicts use the lowercase version of the related Django Setting (e.g. 'REASON_EXPECTED' =>
           'reason_expected').

    Example return value::

        {
            'rest_framework.exceptions:PermissionDenied': {
                'is_ignored': True,
                'log_error': True,
                'log_stack_trace': True,
                'reason_expected': 'In most cases, signifies a user was trying to do something they cannot do. '
                   'However, an overabundance could indicate a bug, which could be monitored for.'
            }
            ...
        }

    """
    global _EXPECTED_ERROR_SETTINGS_DICT

    # Return cached processed mappings if already processed
    if _EXPECTED_ERROR_SETTINGS_DICT is not None:
        return _EXPECTED_ERROR_SETTINGS_DICT

    expected_errors = getattr(settings, 'EXPECTED_ERRORS', None)
    if expected_errors is None:
        _EXPECTED_ERROR_SETTINGS_DICT = {}
        return _EXPECTED_ERROR_SETTINGS_DICT

    # Use temporary variable to build mappings to avoid multi-threading issue with a partially
    # processed map.  Worst case, it is processed more than once at start-up.
    expected_error_settings_dict = {}

    try:
        for index, expected_error in enumerate(expected_errors):
            module_and_class = expected_error.get('MODULE_AND_CLASS')
            processed_expected_error = {
                'is_ignored': expected_error.get('IS_IGNORED', True),
                'log_error': expected_error.get('LOG_ERROR', False),
                'log_stack_trace': expected_error.get('LOG_STACK_TRACE', False),
                'reason_expected': expected_error.get('REASON_EXPECTED'),
            }

            # validate configuration
            if not isinstance(module_and_class, str):
                log.error(
                    "Skipping EXPECTED_ERRORS[%d] setting. 'MODULE_AND_CLASS' set to [%s] and should be module.Class, "
                    "like 'rest_framework.exceptions.PermissionDenied'.",
                    index, module_and_class
                )
                continue
            if ':' in module_and_class:
                log.warning(
                    "Replacing ':' with '.' in EXPECTED_ERRORS[%d]['MODULE_AND_CLASS'], which was set to %s. Note that "
                    "monitoring and logging will not include the ':'.",
                    index, module_and_class
                )
                module_and_class = module_and_class.replace(":", ".")
            if module_and_class in expected_error_settings_dict:
                log.warning(
                    "EXPECTED_ERRORS[%d] setting is overriding an earlier setting. 'MODULE_AND_CLASS' [%s] is defined "
                    "multiple times.",
                    index, module_and_class
                )
            if not processed_expected_error['reason_expected']:
                log.error(
                    "Skipping EXPECTED_ERRORS[%d] setting. 'REASON_EXPECTED' is required to document why %s is an "
                    "expected error.",
                    index, module_and_class
                )
                continue
            expected_error_settings_dict[module_and_class] = processed_expected_error
    except Exception as e:  # pylint: disable=broad-except
        set_custom_attribute('expected_errors_setting_misconfigured', repr(e))
        log.exception(f'Error processing setting EXPECTED_ERRORS. {repr(e)}')

    _EXPECTED_ERROR_SETTINGS_DICT = expected_error_settings_dict
    return _EXPECTED_ERROR_SETTINGS_DICT


def clear_cached_expected_error_settings():
    """
    Clears the cached expected error settings. Useful for testing.
    """
    global _EXPECTED_ERROR_SETTINGS_DICT
    _EXPECTED_ERROR_SETTINGS_DICT = None


def _log_and_monitor_expected_errors(request, exception, caller):
    """
    Adds logging and monitoring for expected errors as needed.

    Arguments:
        request: The request
        exception: The exception
        caller: Either 'middleware' or 'drf`
    """
    expected_error_settings_dict = _get_expected_error_settings_dict()
    if not expected_error_settings_dict:
        return

    # 'module.Class', for example, 'django.core.exceptions.PermissionDenied'
    # Note: `Exception` itself doesn't have a module.
    exception_module = getattr(exception, '__module__', '')
    separator = '.' if exception_module else ''
    module_and_class = f'{exception_module}{separator}{exception.__class__.__name__}'

    # Set checked_error_expected_from custom attribute to potentially help find issues where errors are never processed.
    set_custom_attribute('checked_error_expected_from', caller)

    # check if we already added logging/monitoring from a different caller
    request_cache = RequestCache('openedx.core.lib.request_utils')
    cached_handled_exception = request_cache.get_cached_response('handled_exception')
    if cached_handled_exception.is_found:
        cached_module_and_class = cached_handled_exception.value
        # exception was already processed by a different caller
        if cached_handled_exception.value == module_and_class:
            set_custom_attribute('checked_error_expected_from', 'multiple')
            return

        # We have confirmed using monitoring that it is very rare that middleware and drf handle different uncaught exceptions.
        # We will leave this attribute in place, but it is not worth investing in a workaround, especially given that
        # New Relic now offers its own expected error functionality, and this functionality may be simplified or removed.
        set_custom_attribute('unexpected_multiple_exceptions', cached_module_and_class)
        log.warning(
            "Unexpected scenario where different exceptions are handled by _log_and_monitor_expected_errors. "
            "See 'unexpected_multiple_exceptions' custom attribute. Skipping exception for %s.",
            module_and_class,
        )
        return
    request_cache.set('handled_exception', module_and_class)

    if module_and_class not in expected_error_settings_dict:
        return

    exception_message = str(exception)
    set_custom_attribute('error_expected', True)

    expected_error_settings = expected_error_settings_dict[module_and_class]
    if expected_error_settings['is_ignored']:
        # Additional error details are needed for ignored errors, because they are otherwise
        # not available by our monitoring system, because they have been ignored.
        set_custom_attribute('error_ignored_class', module_and_class)
        set_custom_attribute('error_ignored_message', exception_message)

    if expected_error_settings['log_error']:
        exc_info = exception if expected_error_settings['log_stack_trace'] else None
        request_path = getattr(request, 'path', 'request-path-unknown')
        log.info(
            'Expected error %s: %s: seen for path %s',
            module_and_class,
            exception_message,
            request_path,
            exc_info=exc_info,
        )
