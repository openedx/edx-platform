"""
Middleware for embargoing courses.
"""


from django.shortcuts import redirect
from django.contrib.gis.geoip import GeoIP
from django.contrib.gis.geoip.libgeoip import GEOIP_SETTINGS
from util.request import course_id_from_url
from embargo.models import EmbargoConfig
from ipware.ip import get_ip


class EmbargoMiddleware(object):
    """
    Middleware for embargoing courses

    This is configured by creating ``DarkLangConfig`` rows in the database,
    using the django admin site.
    """

    def process_request(self, request):
        url = request.path
        course_id = course_id_from_url(url)

        # If they're trying to access a course that cares about embargoes
        if course_id in EmbargoConfig.current().embargoed_courses_list:

            # If we're having performance issues, add caching here
            ip = get_ip(request)  # TODO replace this with the actual get_ip function
            country_code_from_ip = GeoIP().country_code(ip)
            is_embargoed = (country_code_from_ip in EmbargoConfig.current().embargoed_countries_list)
            if is_embargoed:
                return redirect('embargo')
