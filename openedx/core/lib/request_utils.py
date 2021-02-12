""" Utility functions related to HTTP requests """

import logging
import re

import crum
from django.conf import settings
from django.test.client import RequestFactory
from django.utils.deprecation import MiddlewareMixin
from edx_django_utils.monitoring import set_custom_attribute
from edx_toggles.toggles import SettingToggle, WaffleFlag
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.views import exception_handler
from six.moves.urllib.parse import urlparse

from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

# accommodates course api urls, excluding any course api routes that do not fall under v*/courses, such as v1/blocks.
COURSE_REGEX = re.compile(r'^(.*?/courses/)(?!v[0-9]+/[^/]+){}'.format(settings.COURSE_ID_PATTERN))

# .. toggle_name: request_utils.capture_cookie_sizes
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enables capturing of cookie sizes for monitoring purposes. This can be useful for tracking
#       down large cookies and avoiding hitting limits on the total size of cookies. See the CookieMonitoringMiddleware
#       docstring for details on the monitoring custom attributes that will be set.
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
        full_url = "http://{site_name}".format(site_name=settings.SITE_NAME)
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

        """
        if not CAPTURE_COOKIE_SIZES.is_enabled():
            return

        # ..setting_name: TOP_N_COOKIES_CAPTURED
        # .. setting_default: 5
        # .. setting_description: The number of the largest cookies to capture when monitoring. Capture fewer cookies
        #       if you need to save on monitoring resources.
        # .. setting_warning: Depends on the `request_utils.capture_cookie_sizes` toggle being enabled.
        top_n_cookies_captured = getattr(settings, "TOP_N_COOKIES_CAPTURED", 5)
        # ..setting_name: TOP_N_COOKIE_GROUPS_CAPTURED
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
        log.debug(u'cookies_total_size = %d', total_cookie_size)

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
        for index, name in enumerate(top_n_cookies, start=1):
            size = names_to_size[name]
            name_attribute = '{}.{}.name'.format(attribute_prefix, index)
            size_attribute = '{}.{}.size'.format(attribute_prefix, index)

            set_custom_attribute(name_attribute, name)
            set_custom_attribute(size_attribute, size)
            log.debug('%s = %d', name, size)

# .. toggle_name: ENABLE_403_MONITORING
# .. toggle_implementation: SettingToggle
# .. toggle_default: False
# .. toggle_description: Temporary toggle to track down the source of 403s for /oauth2/exchange_access_token/.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-02-12
# .. toggle_target_removal_date: 2021-03-12
# .. toggle_tickets: https://openedx.atlassian.net/browse/ARCHBOM-1667
ENABLE_403_MONITORING = SettingToggle('ENABLE_403_MONITORING', default=False, module_name=__name__)


def custom_exception_handler(exc, context):
    """ Enables monitoring of 403s for /oauth2/exchange_access_token/ to gather data. """
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)

    log_403s = ENABLE_403_MONITORING.is_enabled() and response.status_code == 403
    log_403s = log_403s and 'request' in context and context['request'] and context['request'].path
    log_403s = log_403s and context['request'].path.startswith('/oauth2/exchange_access_token/')
    if log_403s:
        set_custom_attribute('exchange_access_token_error', repr(exc))
        log.info('Found 403 in %s', context['request'].path, exc_info=exc, stack_info=True)

    return response
