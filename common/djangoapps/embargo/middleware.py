"""
Middleware for embargoing courses.
"""


from django.shortcuts import redirect
from util.request import course_id_from_url
from embargo.models import EmbargoedCourse, EmbargoedState, IPException
from ipware.ip import get_ip
import pygeoip
from django.conf import settings


class EmbargoMiddleware(object):
    """
    Middleware for embargoing courses

    This is configured by creating ``DarkLangConfig`` rows in the database,
    using the django admin site.
    """

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
            if ip_addr in IPException.current().blacklist_ips:
                return redirect('embargo')

            country_code_from_ip = pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip_addr)
            is_embargoed = country_code_from_ip in EmbargoedState.current().embargoed_countries_list
            # Fail if country is embargoed and the ip address isn't explicitly whitelisted
            if is_embargoed and ip_addr not in IPException.current().whitelist_ips:
                return redirect('embargo')
