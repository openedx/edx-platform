"""
Middleware for embargoing courses.
"""


from django.shortcuts import redirect
from util.request import course_id_from_url
from embargo.models import EmbargoConfig
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
        if course_id in EmbargoConfig.current().embargoed_courses_list:

            # If we're having performance issues, add caching here
            ip = get_ip(request)
            country_code_from_ip = pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip)
            is_embargoed = (country_code_from_ip in EmbargoConfig.current().embargoed_countries_list)
            if is_embargoed:
                return redirect('embargo')
