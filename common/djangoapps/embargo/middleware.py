"""Middleware for embargoing site and courses.

IMPORTANT NOTE: This code WILL NOT WORK if you have a misconfigured proxy
server.  If you are configuring embargo functionality, or if you are
experiencing mysterious problems with embargoing, please check that your
reverse proxy is setting any of the well known client IP address headers (ex.,
HTTP_X_FORWARDED_FOR).

This middleware allows you to:

* Embargoing courses (access restriction by courses)
* Embargoing site (access restriction of the main site)

Embargo can restrict by states and whitelist/blacklist (IP Addresses
(ie. 10.0.0.0) or Networks (ie. 10.0.0.0/24)).

Usage:

# Enable the middleware in your settings

# To enable Embargo for particular courses, set:
FEATURES['EMBARGO'] = True # blocked ip will be redirected to /embargo

# To enable the Embargo feature for the whole site, set:
FEATURES['SITE_EMBARGOED'] = True

# With SITE_EMBARGOED, you can define an external url to redirect with:
EMBARGO_SITE_REDIRECT_URL = 'https://www.edx.org/'

# if EMBARGO_SITE_REDIRECT_URL is missing, a HttpResponseForbidden is returned.

"""
import logging
import pygeoip

from django.core.exceptions import MiddlewareNotUsed
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden
from ipware.ip import get_ip
from util.request import course_id_from_url

from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter

log = logging.getLogger(__name__)


class EmbargoMiddleware(object):
    """
    Middleware for embargoing site and courses

    This is configured by creating ``EmbargoedCourse``, ``EmbargoedState``, and
    optionally ``IPFilter`` rows in the database, using the django admin site.
    """
    def __init__(self):
        self.site_enabled = settings.FEATURES.get('SITE_EMBARGOED', False)
        # If embargoing is turned off, make this middleware do nothing
        if not settings.FEATURES.get('EMBARGO', False) and \
           not self.site_enabled:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        """
        Processes embargo requests
        """
        url = request.path
        course_id = course_id_from_url(url)
        course_is_embargoed = EmbargoedCourse.is_embargoed(course_id)

        # If they're trying to access a course that cares about embargoes
        if self.site_enabled or course_is_embargoed:
            response = redirect('embargo')
            # Set the proper response if site is enabled
            if self.site_enabled:
                redirect_url = getattr(settings, 'EMBARGO_SITE_REDIRECT_URL', None)
                response = HttpResponseRedirect(redirect_url) if redirect_url \
                           else HttpResponseForbidden('Access Denied')

            # If we're having performance issues, add caching here
            ip_addr = get_ip(request)

            # if blacklisted, immediately fail
            if ip_addr in IPFilter.current().blacklist_ips:
                if course_is_embargoed:
                    msg = "Embargo: Restricting IP address %s to course %s because IP is blacklisted." % \
                          (ip_addr, course_id)
                else:
                    msg = "Embargo: Restricting IP address %s because IP is blacklisted." % ip_addr
                log.info(msg)
                return response
            # ipv6 support
            if ip_addr.find(':') >= 0:
                country_code_from_ip = pygeoip.GeoIP(settings.GEOIPV6_PATH).country_code_by_addr(ip_addr)
            else:
                country_code_from_ip = pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip_addr)

            is_embargoed = country_code_from_ip in EmbargoedState.current().embargoed_countries_list
            # Fail if country is embargoed and the ip address isn't explicitly
            # whitelisted
            if is_embargoed and ip_addr not in IPFilter.current().whitelist_ips:
                if course_is_embargoed:
                    msg = "Embargo: Restricting IP address %s to course %s because IP is from country %s." % \
                          (ip_addr, course_id, country_code_from_ip)
                else:
                    msg = "Embargo: Restricting IP address %s because IP is from country %s." % \
                          (ip_addr, country_code_from_ip)

                log.info(msg)
                return response
