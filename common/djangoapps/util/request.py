""" Utility functions related to HTTP requests """
import pygeoip
from django.conf import settings
from microsite_configuration.middleware import MicrositeConfiguration
from django import http

class BlockedIpMiddleware(object):
    """
    simple middlware to block IP addresses
    """
    gi = pygeoip.GeoIP(settings.GEOIP_DAT_LOCATION, pygeoip.MEMORY_CACHE)
    def process_request(self, request):
        ip = request.META['REMOTE_ADDR']
        if self.gi.country_code_by_addr(ip) in settings.LIMIT_ACCESS_COUNTRIES:
            return http.HttpResponseForbidden('<h1>Forbidden</h1>')
        return None

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
        return MicrositeConfiguration.get_microsite_configuration_value('site_domain', settings.SITE_NAME)
