"""
Middleware for Mobile APIs
"""


from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin
from pytz import UTC

from lms.djangoapps.mobile_api.mobile_platform import MobilePlatform
from lms.djangoapps.mobile_api.models import AppVersionConfig
from lms.djangoapps.mobile_api.utils import parsed_version
from openedx.core.lib.cache_utils import get_cache
from openedx.core.lib.mobile_utils import is_request_from_mobile_app


class AppVersionUpgrade(MiddlewareMixin):
    """
    Middleware class to keep track of mobile application version being used.
    """
    LATEST_VERSION_HEADER = 'EDX-APP-LATEST-VERSION'
    LAST_SUPPORTED_DATE_HEADER = 'EDX-APP-VERSION-LAST-SUPPORTED-DATE'
    NO_LAST_SUPPORTED_DATE = 'NO_LAST_SUPPORTED_DATE'
    NO_LATEST_VERSION = 'NO_LATEST_VERSION'
    USER_APP_VERSION = 'USER_APP_VERSION'
    REQUEST_CACHE_NAME = 'app-version-info'
    CACHE_TIMEOUT = settings.APP_UPGRADE_CACHE_TIMEOUT

    def process_request(self, request):
        """
        Processes request to validate app version that is making request.

        Returns:
            Http response with status code 426 (i.e. Update Required) if request is from
            mobile native app and app version is no longer supported else returns None
        """
        version_data = self._get_version_info(request)
        if version_data:
            last_supported_date = version_data[self.LAST_SUPPORTED_DATE_HEADER]
            if last_supported_date != self.NO_LAST_SUPPORTED_DATE:
                if datetime.now().replace(tzinfo=UTC) > last_supported_date:
                    return HttpResponse(status=426)  # Http status 426; Update Required

    def process_response(self, __, response):
        """
        If request is from mobile native app, then add version related info to response headers.

        Returns:
            Http response: with additional headers;
                1. EDX-APP-LATEST-VERSION; if user app version < latest available version
                2. EDX-APP-VERSION-LAST-SUPPORTED-DATE; if user app version < min supported version and
                   timestamp < expiry of that version
        """
        request_cache_dict = get_cache(self.REQUEST_CACHE_NAME)
        if request_cache_dict:
            last_supported_date = request_cache_dict[self.LAST_SUPPORTED_DATE_HEADER]
            if last_supported_date != self.NO_LAST_SUPPORTED_DATE:
                response[self.LAST_SUPPORTED_DATE_HEADER] = last_supported_date.isoformat()
            latest_version = request_cache_dict[self.LATEST_VERSION_HEADER]
            user_app_version = request_cache_dict[self.USER_APP_VERSION]
            if (latest_version != self.NO_LATEST_VERSION and
                    parsed_version(user_app_version) < parsed_version(latest_version)):
                response[self.LATEST_VERSION_HEADER] = latest_version
        return response

    def _get_cache_key_name(self, field, key):
        """
        Get key name to use to cache any property against field name and identification key.

        Arguments:
            field (str): The property name that needs to get cached.
            key (str): Unique identification for cache key (e.g. platform_name).

        Returns:
            string: Cache key to be used.
        """
        return f"mobile_api.app_version_upgrade.{field}.{key}"

    def _get_version_info(self, request):
        """
        Gets and Sets version related info in mem cache and request cache; and returns a dict of it.

        It sets request cache data for last_supported_date and latest_version with memcached values if exists against
        user app properties else computes the values for specific platform and sets it in both memcache (for next
        server interaction from same app version/platform) and request cache

        Returns:
            dict: Containing app version info
        """
        user_agent = request.headers.get('User-Agent')
        if user_agent:
            platform = self._get_platform(request, user_agent)
            if platform:
                request_cache_dict = get_cache(self.REQUEST_CACHE_NAME)
                request_cache_dict[self.USER_APP_VERSION] = platform.version
                last_supported_date_cache_key = self._get_cache_key_name(
                    self.LAST_SUPPORTED_DATE_HEADER,
                    platform.version
                )
                latest_version_cache_key = self._get_cache_key_name(self.LATEST_VERSION_HEADER, platform.NAME)
                cached_data = cache.get_many([last_supported_date_cache_key, latest_version_cache_key])

                last_supported_date = cached_data.get(last_supported_date_cache_key)
                if last_supported_date != self.NO_LAST_SUPPORTED_DATE and not isinstance(last_supported_date, datetime):
                    last_supported_date = self._get_last_supported_date(platform.NAME, platform.version)
                    cache.set(last_supported_date_cache_key, last_supported_date, self.CACHE_TIMEOUT)
                request_cache_dict[self.LAST_SUPPORTED_DATE_HEADER] = last_supported_date

                latest_version = cached_data.get(latest_version_cache_key)
                if not (latest_version and isinstance(latest_version, str)):
                    latest_version = self._get_latest_version(platform.NAME)
                    cache.set(latest_version_cache_key, latest_version, self.CACHE_TIMEOUT)
                request_cache_dict[self.LATEST_VERSION_HEADER] = latest_version

                return request_cache_dict

    def _get_platform(self, request, user_agent):
        """
        Determines the platform type for mobile app making the request against user_agent.

        Returns:
            None if request app does not belong to one of the supported mobile platforms
            else returns an instance of corresponding mobile platform.
        """
        if is_request_from_mobile_app(request):
            return MobilePlatform.get_instance(user_agent)

    def _get_last_supported_date(self, platform_name, platform_version):
        """ Get expiry date of app version for a platform. """
        return AppVersionConfig.last_supported_date(platform_name, platform_version) or self.NO_LAST_SUPPORTED_DATE

    def _get_latest_version(self, platform_name):
        """ Get latest app version available for platform. """
        return AppVersionConfig.latest_version(platform_name) or self.NO_LATEST_VERSION
