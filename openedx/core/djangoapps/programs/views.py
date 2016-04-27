"""
Main views and method related to the Programs.
"""

import logging

from openedx.core.djangoapps.util.helpers import get_id_token
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import programs_api_client, is_student_dashboard_programs_enabled


log = logging.getLogger(__name__)
# OAuth2 Client name for programs
CLIENT_NAME = "programs"


def get_course_programs_for_dashboard(user, course_keys):   # pylint: disable=invalid-name
    """ Return all programs related to a user.

    Given a user and an iterable of course keys, find all
    the programs relevant to the user's dashboard and return them in a
    dictionary keyed by the course_key.

    Arguments:
        user (user object): Currently logged-in User for which we need to get
            JWT ID-Token
        course_keys (list): List of course keys in which user is enrolled

    Returns:
        Dictionary response containing programs or None
    """
    course_programs = {}
    if not is_student_dashboard_programs_enabled():
        log.warning("Programs service for student dashboard is disabled.")
        return course_programs

    # unicode-ify the course keys for efficient lookup
    course_keys = map(unicode, course_keys)

    # get programs slumber-based client 'EdxRestApiClient'
    try:
        api_client = programs_api_client(ProgramsApiConfig.current().internal_api_url, get_id_token(user, CLIENT_NAME))
    except Exception:   # pylint: disable=broad-except
        log.exception('Failed to initialize the Programs API client.')
        return course_programs

    # get programs from api client
    try:
        response = api_client.programs.get()
    except Exception:  # pylint: disable=broad-except
        log.exception('Failed to retrieve programs from the Programs API.')
        return course_programs

    programs = response.get('results', [])
    if not programs:
        log.warning("No programs found for the user '%s'.", user.id)
        return course_programs

    # reindex the result from pgm -> course code -> course run
    #  to
    # course run -> program, ignoring course runs not present in the dashboard enrollments
    for program in programs:
        try:
            for course_code in program['course_codes']:
                for run in course_code['run_modes']:
                    if run['course_key'] in course_keys:
                        course_programs[run['course_key']] = program
        except KeyError:
            log.exception('Unable to parse Programs API response: %r', program)

    return course_programs
