"""
Middleware for embargoing courses.

IMPORTANT NOTE: This code WILL NOT WORK if you have a misconfigured proxy
server.  If you are configuring embargo functionality, or if you are
experiencing mysterious problems with embargoing, please check that your
reverse proxy is setting any of the well known client IP address headers (ex.,
HTTP_X_FORWARDED_FOR).
"""

import pygeoip
import django.core.exceptions

from django.conf import settings
from django.shortcuts import redirect
from ipware.ip import get_ip
from util.request import course_id_from_url

from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter


class EmbargoMiddleware(object):
    """
    Middleware for embargoing courses

    This is configured by creating ``EmbargoedCourse``, ``EmbargoedState``, and
    optionally ``IPFilter`` rows in the database, using the django admin site.
    """
    def __init__(self):
        # If embargoing is not turned out, make this middleware do nothing
        if not settings.FEATURES.get('EMBARGO', False):
            self.process_request = self.return_unaltered

    def return_unaltered(self, request):
        return

    def __init__(self):
        # If embargoing is turned off, make this middleware do nothing
        if settings.FEATURES.get('EMBARGO', False):
            raise django.core.exceptions.MiddlewareNotUsed()

    def process_request(self, request):
        """
        Processes embargo requests
        """
        url = request.path
        course_id = course_id_from_url(url)

        # If they're trying to access a course that cares about embargoes
        if EmbargoedCourse.is_embargoed(course_id):
            # If we're having performance issues, add caching here
            ip_addr = get_ip(request)

            # if blacklisted, immediately fail
            if ip_addr in IPFilter.current().blacklist_ips:
                return redirect('embargo')

            country_code_from_ip = pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip_addr)
            is_embargoed = country_code_from_ip in EmbargoedState.current().embargoed_countries_list
            # Fail if country is embargoed and the ip address isn't explicitly whitelisted
            if is_embargoed and ip_addr not in IPFilter.current().whitelist_ips:
                return redirect('embargo')
