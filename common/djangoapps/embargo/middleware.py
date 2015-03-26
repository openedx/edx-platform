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

# Enable the middleware in your settings

# To enable Embargo for particular courses, set:
FEATURES['EMBARGO'] = True # blocked ip will be redirected to /embargo

# To enable the Embargo feature for the whole site, set:
FEATURES['SITE_EMBARGOED'] = True

# With SITE_EMBARGOED, you can define an external url to redirect with:
EMBARGO_SITE_REDIRECT_URL = 'https://www.edx.org/'

# if EMBARGO_SITE_REDIRECT_URL is missing, a HttpResponseForbidden is returned.

"""
from functools import partial
import logging
import pygeoip
from lazy import lazy

from django.core.exceptions import MiddlewareNotUsed
from django.core.cache import cache
from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseRedirect, HttpResponseForbidden
from ipware.ip import get_ip
from util.request import course_id_from_url

from student.models import unique_id_for_user
from embargo.models import EmbargoedCourse, EmbargoedState, IPFilter

log = logging.getLogger(__name__)


class EmbargoMiddleware(object):
    """
    Middleware for embargoing site and courses

    This is configured by creating ``EmbargoedCourse``, ``EmbargoedState``, and
    optionally ``IPFilter`` rows in the database, using the django admin site.
    """

    # Reasons a user might be blocked.
    # These are used to generate info messages in the logs.
    REASONS = {
        "ip_blacklist": u"Restricting IP address {ip_addr} {from_course} because IP is blacklisted.",
        "ip_country": u"Restricting IP address {ip_addr} {from_course} because IP is from country {ip_country}.",
        "profile_country": (
            u"Restricting user {user_id} {from_course} because "
            u"the user set the profile country to {profile_country}."
        )
    }

    def __init__(self):
        self.site_enabled = settings.FEATURES.get('SITE_EMBARGOED', False)
        # If embargoing is turned off, make this middleware do nothing
        if not settings.FEATURES.get('EMBARGO', False) and not self.site_enabled:
            raise MiddlewareNotUsed()

    def process_request(self, request):
        """
        Processes embargo requests.
        """
        url = request.path
        course_id = course_id_from_url(url)
        course_is_embargoed = EmbargoedCourse.is_embargoed(course_id)

        # If they're trying to access a course that cares about embargoes
        if self.site_enabled or course_is_embargoed:

            # Construct the list of functions that check whether the user is embargoed.
            # We wrap each of these functions in a decorator that logs the reason the user
            # was blocked.
            # Each function should return `True` iff the user is blocked by an embargo.
            check_functions = [
                self._log_embargo_reason(check_func, course_id, course_is_embargoed)
                for check_func in [
                    partial(self._is_embargoed_by_ip, get_ip(request)),
                    partial(self._is_embargoed_by_profile_country, request.user)
                ]
            ]

            # Perform each of the checks
            # If the user fails any of the checks, immediately redirect them
            # and skip later checks.
            for check_func in check_functions:
                if check_func():
                    return self._embargo_redirect_response

        # If all the check functions pass, implicitly return None
        # so that the middleware processor can continue processing
        # the response.

    def _is_embargoed_by_ip(self, ip_addr, course_id=u"", course_is_embargoed=False):
        """
        Check whether the user is embargoed based on the IP address.

        Args:
            ip_addr (str): The IP address the request originated from.

        Keyword Args:
            course_id (unicode): The course the user is trying to access.
            course_is_embargoed (boolean): Whether the course the user is accessing has been embargoed.

        Returns:
            A unicode message if the user is embargoed, otherwise `None`

        """
        # If blacklisted, immediately fail
        if ip_addr in IPFilter.current().blacklist_ips:
            return self.REASONS['ip_blacklist'].format(
                ip_addr=ip_addr,
                from_course=self._from_course_msg(course_id, course_is_embargoed)
            )

        # If we're white-listed, then allow access
        if ip_addr in IPFilter.current().whitelist_ips:
            return None

        # Retrieve the country code from the IP address
        # and check it against the list of embargoed countries
        ip_country = self._country_code_from_ip(ip_addr)
        if ip_country in self._embargoed_countries:
            return self.REASONS['ip_country'].format(
                ip_addr=ip_addr,
                ip_country=ip_country,
                from_course=self._from_course_msg(course_id, course_is_embargoed)
            )

        # If none of the other checks caught anything,
        # implicitly return None to indicate that the user can access the course

    def _is_embargoed_by_profile_country(self, user, course_id="", course_is_embargoed=False):
        """
        Check whether the user is embargoed based on the country code in the user's profile.

        Args:
            user (User): The user attempting to access courseware.

        Keyword Args:
            course_id (unicode): The course the user is trying to access.
            course_is_embargoed (boolean): Whether the course the user is accessing has been embargoed.

        Returns:
            A unicode message if the user is embargoed, otherwise `None`

        """
        cache_key = u'user.{user_id}.profile.country'.format(user_id=user.id)
        profile_country = cache.get(cache_key)
        if profile_country is None:
            profile = getattr(user, 'profile', None)
            if profile is not None and profile.country.code is not None:
                profile_country = profile.country.code.upper()
            else:
                profile_country = ""
            cache.set(cache_key, profile_country)

        if profile_country in self._embargoed_countries:
            return self.REASONS['profile_country'].format(
                user_id=unique_id_for_user(user),
                profile_country=profile_country,
                from_course=self._from_course_msg(course_id, course_is_embargoed)
            )
        else:
            return None

    def _country_code_from_ip(self, ip_addr):
        """
        Return the country code associated with an IP address.
        Handles both IPv4 and IPv6 addresses.

        Args:
            ip_addr (str): The IP address to look up.

        Returns:
            str: A 2-letter country code.

        """
        if ip_addr.find(':') >= 0:
            return pygeoip.GeoIP(settings.GEOIPV6_PATH).country_code_by_addr(ip_addr)
        else:
            return pygeoip.GeoIP(settings.GEOIP_PATH).country_code_by_addr(ip_addr)

    @property
    def _embargo_redirect_response(self):
        """
        The HTTP response to send when the user is blocked from a course.
        This will either be a redirect to a URL configured in Django settings
        or a forbidden response.

        Returns:
            HTTPResponse

        """
        response = redirect('embargo')

        # Set the proper response if site is enabled
        if self.site_enabled:
            redirect_url = getattr(settings, 'EMBARGO_SITE_REDIRECT_URL', None)
            response = (
                HttpResponseRedirect(redirect_url)
                if redirect_url
                else HttpResponseForbidden('Access Denied')
            )

        return response

    @lazy
    def _embargoed_countries(self):
        """
        Return the list of 2-letter country codes for embargoed countries.
        The result is cached within the scope of the response.

        Returns:
            list

        """
        return EmbargoedState.current().embargoed_countries_list

    def _from_course_msg(self, course_id, course_is_embargoed):
        """
        Format a message indicating whether the user was blocked from a specific course.
        This can be used in info messages, but should not be used in user-facing messages.

        Args:
            course_id (unicode): The ID of the course being accessed.
            course_is_embarged (boolean): Whether the course being accessed is embargoed.

        Returns:
            unicode

        """
        return (
            u"from course {course_id}".format(course_id=course_id)
            if course_is_embargoed
            else u""
        )

    def _log_embargo_reason(self, check_func, course_id, course_is_embargoed):
        """
        Decorator for embargo check functions that will:
            * execute the check function
            * check whether the user is blocked by an embargo, and if so, log the reason
            * return a boolean indicating whether the user was blocked.

        Args:
            check_func (partial): A function that should return unicode reason if the user
                was blocked, otherwise should return None.  This function will be passed
                `course_id` and `course_is_embarged` kwargs so it can format a detailed
                reason message.

            course_id (unicode): The ID of the course the user is trying to access.

            course_is_embargoed (boolean): Whether the course the user is trying
                to access is under an embargo.

        Returns:
            boolean: True iff the user was blocked by an embargo

        """
        def _inner():
            # Perform the check and retrieve the reason string.
            # The reason will be `None` if the user passes the check and can access the course.
            # We pass in the course ID and whether the course is embargoed
            # so that the check function can fill in the "reason" message with more specific details.
            reason = check_func(
                course_id=course_id,
                course_is_embargoed=course_is_embargoed
            )

            # If the reason was `None`, indicate that the user was not blocked.
            if reason is None:
                return False

            # Otherwise, log the reason the user was blocked
            # and return True.
            else:
                msg = u"Embargo: {reason}".format(reason=reason)
                log.info(msg)
                return True

        return _inner
