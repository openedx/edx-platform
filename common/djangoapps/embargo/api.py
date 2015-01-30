"""
The Python API layer of the country access settings. Essentially the middle tier of the project, responsible for all
business logic that is not directly tied to the data itself.

This API is exposed via the middleware(emabargo/middileware.py) layer but may be used directly in-process.

"""
import logging
import pygeoip

from django.core.cache import cache
from django.conf import settings
from embargo.models import CountryAccessRule, RestrictedCourse

log = logging.getLogger(__name__)


def get_user_country_from_profile(user):
    """
    Check whether the user is embargoed based on the country code in the user's profile.

    Args:
        user (User): The user attempting to access courseware.

    Returns:
        user country from profile.

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

    return profile_country


def _country_code_from_ip(ip_addr):
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


def check_course_access(user, ip_address, course_key):
    """
    Check is the user with this ip_address has access to the given course

    Params:
        user (User): Currently logged in user object
        ip_address (str): The ip_address of user
        course_key (CourseLocator): CourseLocator object the user is trying to access

    Returns:
        The return will be True if the user has access on the course.
        if any constraints fails it will return the False
    """
    course_is_restricted = RestrictedCourse.is_restricted_course(course_key)
    # If they're trying to access a course that cares about embargoes

    # If course is not restricted then return immediately return True
    # no need for further checking
    if not course_is_restricted:
        return True

    # Retrieve the country code from the IP address
    # and check it against the allowed countries list for a course
    user_country_from_ip = _country_code_from_ip(ip_address)
    # if user country has access to course return True
    if not CountryAccessRule.check_country_access(course_key, user_country_from_ip):
        return False

    # Retrieve the country code from the user profile.
    user_country_from_profile = get_user_country_from_profile(user)
    # if profile country has access return True
    if not CountryAccessRule.check_country_access(course_key, user_country_from_profile):
        return False

    return True
