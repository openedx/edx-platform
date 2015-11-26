"""
Helper methods for Programs.
"""
from django.core.cache import cache
from edx_rest_api_client.client import EdxRestApiClient
from openedx.core.djangoapps.programs.models import ProgramsApiConfig


def is_student_dashboard_programs_enabled():    # pylint: disable=invalid-name
    """ Returns a Boolean indicating whether LMS dashboard functionality
     related to Programs should be enabled or not.
    """
    return ProgramsApiConfig.current().is_student_dashboard_enabled


def programs_api_client(api_url, jwt_access_token):
    """ Returns an Programs API client setup with authentication for the
    specified user.
    """
    return EdxRestApiClient(
        api_url,
        jwt=jwt_access_token
    )


def is_cache_enabled_for_programs():
    """Returns a Boolean indicating whether responses from the Programs API
    will be cached.
    """
    return ProgramsApiConfig.current().is_cache_enabled


def set_cached_programs_response(programs_data):
    """ Set cache value for the programs data with specific ttl.

    Arguments:
        programs_data (dict): Programs data in dictionary format
    """
    cache.set(
        ProgramsApiConfig.PROGRAMS_API_CACHE_KEY,
        programs_data,
        ProgramsApiConfig.current().cache_ttl
    )


def get_cached_programs_response():
    """ Get programs data from cache against cache key."""
    cache_key = ProgramsApiConfig.PROGRAMS_API_CACHE_KEY
    return cache.get(cache_key)
