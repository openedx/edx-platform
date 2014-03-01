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

# To enable Embargoing by courses, add:
FEATURES['EMBARGO'] = True # blocked ip will be redirected to /embargo

# To enable Embargoing site:
FEATURES['EMBARGO_SITE'] = True

# With EMBARGO_SITE, you can define an external to redirect with:
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
        self.site_enabled = settings.FEATURES.get('EMBARGO_SITE', False)
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

        # If they're trying to access a course that cares about embargoes
        if self.site_enabled or EmbargoedCourse.is_embargoed(course_id):
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
                log.info("Embargo: Restricting IP address %s because IP is blacklisted.", ip_addr)
                return response

            country_code_from_ip = pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip_addr)
            is_embargoed = country_code_from_ip in EmbargoedState.current().embargoed_countries_list
            # Fail if country is embargoed and the ip address isn't explicitly whitelisted
            if is_embargoed and ip_addr not in IPFilter.current().whitelist_ips:
                log.info(
                    "Embargo: Restricting IP address %s because IP is from country %s.",
                    ip_addr, country_code_from_ip
                )
                return response
