"""
The Python API layer of the country access settings. Essentially the middle tier of the project, responsible for all
business logic that is not directly tied to the data itself.

This API is exposed via the middleware(emabargo/middileware.py) layer but may be used directly in-process.

"""
import logging
import pygeoip

from django.core.cache import cache
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status
from ipware.ip import get_ip

from student.auth import has_course_author_access
from .models import CountryAccessRule, RestrictedCourse


log = logging.getLogger(__name__)


def redirect_if_blocked(course_key, access_point='enrollment', **kwargs):
    """Redirect if the user does not have access to the course. In case of blocked if access_point
    is not enrollment and course has enabled is_disabled_access_check then user can view that course.

    Arguments:
        course_key (CourseKey): Location of the course the user is trying to access.

    Keyword Arguments:
        Same as `check_course_access` and `message_url_path`

    """
    if settings.FEATURES.get('EMBARGO'):
        is_blocked = not check_course_access(course_key, **kwargs)
        if is_blocked:
            if access_point == "courseware":
                if not RestrictedCourse.is_disabled_access_check(course_key):
                    return message_url_path(course_key, access_point)
            else:
                return message_url_path(course_key, access_point)


def check_course_access(course_key, user=None, ip_address=None, url=None):
    """
    Check is the user with this ip_address has access to the given course

    Arguments:
        course_key (CourseKey): Location of the course the user is trying to access.

    Keyword Arguments:
        user (User): The user making the request.  Can be None, in which case
            the user's profile country will not be checked.
        ip_address (str): The IP address of the request.
        url (str): The URL the user is trying to access.  Used in
            log messages.

    Returns:
        Boolean: True if the user has access to the course; False otherwise

    """
    # No-op if the country access feature is not enabled
    if not settings.FEATURES.get('EMBARGO'):
        return True

    # First, check whether there are any restrictions on the course.
    # If not, then we do not need to do any further checks
    course_is_restricted = RestrictedCourse.is_restricted_course(course_key)

    if not course_is_restricted:
        return True

    # Always give global and course staff access, regardless of embargo settings.
    if user is not None and has_course_author_access(user, course_key):
        return True

    if ip_address is not None:
        # Retrieve the country code from the IP address
        # and check it against the allowed countries list for a course
        user_country_from_ip = _country_code_from_ip(ip_address)

        if not CountryAccessRule.check_country_access(course_key, user_country_from_ip):
            log.info(
                (
                    u"Blocking user %s from accessing course %s at %s "
                    u"because the user's IP address %s appears to be "
                    u"located in %s."
                ),
                getattr(user, 'id', '<Not Authenticated>'),
                course_key,
                url,
                ip_address,
                user_country_from_ip
            )
            return False

    if user is not None:
        # Retrieve the country code from the user's profile
        # and check it against the allowed countries list for a course.
        user_country_from_profile = _get_user_country_from_profile(user)

        if not CountryAccessRule.check_country_access(course_key, user_country_from_profile):
            log.info(
                (
                    u"Blocking user %s from accessing course %s at %s "
                    u"because the user's profile country is %s."
                ),
                user.id, course_key, url, user_country_from_profile
            )
            return False

    return True


def message_url_path(course_key, access_point):
    """Determine the URL path for the message explaining why the user was blocked.

    This is configured per-course.  See `RestrictedCourse` in the `embargo.models`
    module for more details.

    Arguments:
        course_key (CourseKey): The location of the course.
        access_point (str): How the user was trying to access the course.
            Can be either "enrollment" or "courseware".

    Returns:
        unicode: The URL path to a page explaining why the user was blocked.

    Raises:
        InvalidAccessPoint: Raised if access_point is not a supported value.

    """
    return RestrictedCourse.message_url_path(course_key, access_point)


def _get_user_country_from_profile(user):
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


def get_embargo_response(request, course_id, user):
    """
    Check whether any country access rules block the user from enrollment.

    Args:
        request (HttpRequest): The request object
        course_id (str): The requested course ID
        user (str): The current user object

    Returns:
        HttpResponse: Response of the embargo page if embargoed, None if not

    """
    redirect_url = redirect_if_blocked(
        course_id, user=user, ip_address=get_ip(request), url=request.path)
    if redirect_url:
        return Response(
            status=status.HTTP_403_FORBIDDEN,
            data={
                "message": (
                    u"Users from this location cannot access the course '{course_id}'."
                ).format(course_id=course_id),
                "user_message_url": request.build_absolute_uri(redirect_url)
            }
        )
