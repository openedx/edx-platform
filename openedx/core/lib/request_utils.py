""" Utility functions related to HTTP requests """

import logging
import re
from urllib.parse import urlparse

import crum
from django.conf import settings
from django.test.client import RequestFactory
from django.utils.deprecation import MiddlewareMixin
from edx_django_utils.cache import RequestCache
from edx_django_utils.monitoring import set_custom_attribute
from edx_toggles.toggles import WaffleFlag
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import exception_handler
from common.djangoapps.util.log_sensitive import encrypt_for_log

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# accommodates course api urls, excluding any course api routes that do not fall under v*/courses, such as v1/blocks.
COURSE_REGEX = re.compile(fr'^(.*?/course(s)?/)(?!v[0-9]+/[^/]+){settings.COURSE_ID_PATTERN}')

# .. toggle_name: request_utils.capture_cookie_sizes
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables more detailed capturing of cookie sizes for monitoring purposes. This can be useful for tracking
#       down large cookies if requests are nearing limits on the total size of cookies. See the
#       CookieMonitoringMiddleware docstring for details on the monitoring custom attributes that will be set.
# .. toggle_warnings: Enabling this flag will add a number of custom attributes, and could adversely affect other
#       monitoring. Only enable temporarily, or lower TOP_N_COOKIES_CAPTURED and TOP_N_COOKIE_GROUPS_CAPTURED django
#       settings to capture less data.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2019-02-22
CAPTURE_COOKIE_SIZES = WaffleFlag('request_utils.capture_cookie_sizes', __name__)
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


class CookieMonitoringMiddleware(MiddlewareMixin):
    """
    Middleware for monitoring the size and growth of all our cookies, to see if
    we're running into browser limits.
    """
    def process_request(self, request):
        """
        Emit custom attributes for cookie size values for every cookie we have.

        Don't log contents of cookies because that might cause a security issue.
        We just want to see if any cookies are growing out of control.

        A useful NRQL Query:
            SELECT count(*), max(`cookies.max.group.size`) from Transaction FACET
            `cookies.max.group.name`

            SELECT * FROM Transaction WHERE cookies_total_size > 6000

        Attributes that are added by this middleware:

        cookies.header.size: The total size in bytes of the cookie header

        If CAPTURE_COOKIE_SIZES is enabled, additional attributes will be added:

        cookies.<N>.name: The name of the Nth largest cookie
        cookies.<N>.size: The size of the Nth largest cookie
        cookies..group.<N>.name: The name of the Nth largest cookie.
        cookies.group.<N>.size: The size of the Nth largest cookie group.
        cookies.max.name: The name of the largest cookie sent by the user.
        cookies.max.size: The size of the largest cookie sent by the user.
        cookies.max.group.name: The name of the largest group of cookies. A single cookie
            counts as a group of one for this calculation.
        cookies.max.group.size: The sum total size of all the cookies in the largest group.
        cookies_total_size: The sum total size of all cookies in this request.

        Related Settings (see annotations for details):

        - `request_utils.capture_cookie_sizes`
        - TOP_N_COOKIES_CAPTURED
        - TOP_N_COOKIE_GROUPS_CAPTURED
        - COOKIE_SIZE_LOGGING_THRESHOLD
        - COOKIE_HEADER_DEBUG_PUBLIC_KEY

        """

        raw_header_cookie = request.META.get('HTTP_COOKIE', '')
        cookie_header_size = len(raw_header_cookie.encode('utf-8'))
        set_custom_attribute('cookies.header.size', cookie_header_size)

        # .. setting_name: COOKIE_SIZE_LOGGING_THRESHOLD
        # .. setting_default: None
        # .. setting_description: The minimum size for logging the entire (encrypted) cookie header. Should be set
        # to a relatively high threshold (suggested 9-10K) to avoid flooding the logs.
        # .. setting_warning: Requires COOKIE_HEADER_DEBUG_PUBLIC_KEY to be set
        logging_threshold = getattr(settings, "COOKIE_SIZE_LOGGING_THRESHOLD", None)

        # .. setting_name: COOKIE_HEADER_DEBUG_PUBLIC_KEY
        # .. setting_default: None
        # .. setting_description: The public key used to encrypt large cookie headers. See See
        #       https://github.com/edx/edx-platform/blob/master/common/djangoapps/util/log_sensitive.py
        #       for instructions on decrypting.
        debug_key = getattr(settings, "COOKIE_HEADER_DEBUG_PUBLIC_KEY", None)

        if logging_threshold and cookie_header_size > logging_threshold:
            if not debug_key:
                log.warning("COOKIE_SIZE_LOGGING_THRESHOLD set without COOKIE_HEADER_DEBUG_PUBLIC_KEY")
            else:
                encrypted_cookie_header = encrypt_for_log(str(raw_header_cookie),
                                                          debug_key)
                log.info(f"Large (> {logging_threshold}) cookie header detected."
                         f" Encrypted contents: {encrypted_cookie_header}")

        if not CAPTURE_COOKIE_SIZES.is_enabled():
            return

        # .. setting_name: TOP_N_COOKIES_CAPTURED
        # .. setting_default: 8
        # .. setting_description: The number of the largest cookies to capture when monitoring. Capture fewer cookies
        #       if you need to save on monitoring resources.
        # .. setting_warning: Depends on the `request_utils.capture_cookie_sizes` toggle being enabled.
        top_n_cookies_captured = getattr(settings, "TOP_N_COOKIES_CAPTURED", 8)
        # .. setting_name: TOP_N_COOKIE_GROUPS_CAPTURED
        # .. setting_default: 5
        # .. setting_description: The number of the largest cookie groups to capture when monitoring. Capture
        #       fewer cookies if you need to save on monitoring resources.
        # .. setting_warning: Depends on the `request_utils.capture_cookie_sizes` toggle being enabled.
        top_n_cookie_groups_captured = getattr(settings, "TOP_N_COOKIE_GROUPS_CAPTURED", 5)

        cookie_names_to_size = {}
        cookie_groups_to_size = {}

        for name, value in request.COOKIES.items():
            # Get cookie size for all cookies.
            cookie_size = len(value)
            cookie_names_to_size[name] = cookie_size

            # Group cookies by their prefix seperated by a period or underscore
            grouping_name = re.split('[._]', name, 1)[0]
            if grouping_name and grouping_name != name:
                # Add or update the size for this group.
                cookie_groups_to_size[grouping_name] = cookie_groups_to_size.get(grouping_name, 0) + cookie_size

        if cookie_names_to_size:
            self.set_custom_attributes_for_top_n(
                cookie_names_to_size,
                top_n_cookies_captured,
                attribute_prefix='cookies',
            )

            max_cookie_name = max(cookie_names_to_size, key=lambda name: cookie_names_to_size[name])
            max_cookie_size = cookie_names_to_size[max_cookie_name]

            set_custom_attribute('cookies.max.name', max_cookie_name)
            set_custom_attribute('cookies.max.size', max_cookie_size)

        if cookie_groups_to_size:
            self.set_custom_attributes_for_top_n(
                cookie_groups_to_size,
                top_n_cookie_groups_captured,
                attribute_prefix='cookies.group',
            )

            max_group_cookie_name = max(cookie_groups_to_size, key=lambda name: cookie_groups_to_size[name])
            max_group_cookie_size = cookie_groups_to_size[max_group_cookie_name]

            # If a single cookies is bigger than any group of cookies, we want max_group... to reflect that.
            # Treating an individual cookie as a group of 1 for calculating the max.
            if max_group_cookie_size < max_cookie_size:
                max_group_cookie_name = max_cookie_name
                max_group_cookie_size = max_cookie_size

            set_custom_attribute('cookies.max.group.name', max_group_cookie_name)
            set_custom_attribute('cookies.max.group.size', max_group_cookie_size)

        total_cookie_size = sum(cookie_names_to_size.values())
        set_custom_attribute('cookies_total_size', total_cookie_size)
        log.debug('cookies_total_size = %d', total_cookie_size)

        top_n_cookies = sorted(
            cookie_names_to_size,
            key=lambda x: cookie_names_to_size[x],
            reverse=True,
        )[:top_n_cookies_captured]
        top_n_cookies_size = sum([cookie_names_to_size[name] for name in top_n_cookies])
        set_custom_attribute('cookies_unaccounted_size', total_cookie_size - top_n_cookies_size)

        set_custom_attribute('cookies_total_num', len(cookie_names_to_size))

    def set_custom_attributes_for_top_n(self, names_to_size, top_n_captured, attribute_prefix):
        """
        Sets custom metric for the top N biggest cookies or cookie groups.

        Arguments:
            names_to_size: Dict of sizes keyed by cookie name or cookie group name
            top_n_captured: Number of largest sizes to monitor.
            attribute_prefix: Prefix (cookies|cookies.group) to use in the custom attribute name.
        """
        top_n_cookies = sorted(
            names_to_size,
            key=lambda x: names_to_size[x],
            reverse=True,
        )[:top_n_captured]
        for count, name in enumerate(top_n_cookies, start=1):
            size = names_to_size[name]
            name_attribute = f'{attribute_prefix}.{count}.name'
            size_attribute = f'{attribute_prefix}.{count}.size'

            set_custom_attribute(name_attribute, name)
            set_custom_attribute(size_attribute, size)
            log.debug('%s = %d', name, size)


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
# .. toggle_warnings: Requires ``LOG_ERROR`` to be set to True, otherwise this value will be ignored.
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
