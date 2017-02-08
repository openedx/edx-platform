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
(ie. 10.0.0.0), Networks (ie. 10.0.0.0/24)), or the user profile country.

Usage:

1) Enable embargo by setting `settings.FEATURES['EMBARGO']` to True.

2) In Django admin, create a new `IPFilter` model to block or whitelist
    an IP address from accessing the site.

3) In Django admin, create a new `RestrictedCourse` model and
    configure a whitelist or blacklist of countries for that course.

"""
import logging
import re

from django.core.exceptions import MiddlewareNotUsed
from django.core.urlresolvers import reverse
from django.conf import settings
from django.shortcuts import redirect
from ipware.ip import get_ip
from util.request import course_id_from_url

from .models import IPFilter
from . import api as embargo_api


log = logging.getLogger(__name__)


class EmbargoMiddleware(object):
    """Middleware for embargoing site and courses. """

    ALLOW_URL_PATTERNS = [
        # Don't block the embargo message pages; otherwise we'd
        # end up in an infinite redirect loop.
        re.compile(r'^/embargo/blocked-message/'),

        # Don't block the Django admin pages.  Otherwise, we might
        # accidentally lock ourselves out of Django admin
        # during testing.
        re.compile(r'^/admin/'),

        # Do not block access to course metadata. This information is needed for
        # sever-to-server calls.
        re.compile(r'^/api/course_structure/v[\d+]/courses/{}/$'.format(settings.COURSE_ID_PATTERN)),
    ]

    def __init__(self):
        # If embargoing is turned off, make this middleware do nothing
        if not settings.FEATURES.get('EMBARGO'):
            raise MiddlewareNotUsed()

    def process_request(self, request):
        """Block requests based on embargo rules.

        This will perform the following checks:

        1) If the user's IP address is blacklisted, block.
        2) If the user's IP address is whitelisted, allow.
        3) If the user's country (inferred from their IP address) is blocked for
            a courseware page, block.
        4) If the user's country (retrieved from the user's profile) is blocked
            for a courseware page, block.
        5) Allow access.

        """
        # Never block certain patterns by IP address
        for pattern in self.ALLOW_URL_PATTERNS:
            if pattern.match(request.path) is not None:
                return None

        ip_address = get_ip(request)
        ip_filter = IPFilter.current()

        if ip_filter.enabled and ip_address in ip_filter.blacklist_ips:
            log.info(
                (
                    u"User %s was blocked from accessing %s "
                    u"because IP address %s is blacklisted."
                ), request.user.id, request.path, ip_address
            )

            # If the IP is blacklisted, reject.
            # This applies to any request, not just courseware URLs.
            ip_blacklist_url = reverse(
                'embargo_blocked_message',
                kwargs={
                    'access_point': 'courseware',
                    'message_key': 'embargo'
                }
            )
            return redirect(ip_blacklist_url)

        elif ip_filter.enabled and ip_address in ip_filter.whitelist_ips:
            log.info(
                (
                    u"User %s was allowed access to %s because "
                    u"IP address %s is whitelisted."
                ),
                request.user.id, request.path, ip_address
            )

            # If the IP is whitelisted, then allow access,
            # skipping later checks.
            return None

        else:
            # Otherwise, perform the country access checks.
            # This applies only to courseware URLs.
            return self.country_access_rules(request.user, ip_address, request.path)

    def country_access_rules(self, user, ip_address, url_path):
        """
        Check the country access rules for a given course.
        Applies only to courseware URLs.

        Args:
            user (User): The user making the current request.
            ip_address (str): The IP address from which the request originated.
            url_path (str): The request path.

        Returns:
            HttpResponse or None

        """
        course_id = course_id_from_url(url_path)

        if course_id:
            redirect_url = embargo_api.redirect_if_blocked(
                course_id,
                user=user,
                ip_address=ip_address,
                url=url_path,
                access_point='courseware'
            )

            if redirect_url:
                return redirect(redirect_url)
