"""
Helper methods for Programs.
"""
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
