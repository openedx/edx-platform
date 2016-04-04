"""Helper functions for working with Programs."""
import logging

from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.lib.edx_api_utils import get_edx_api_data


log = logging.getLogger(__name__)


def get_programs(user):
    """Given a user, get programs from the Programs service.
    Returned value is cached depending on user permissions. Staff users making requests
    against Programs will receive unpublished programs, while regular users will only receive
    published programs.

    Arguments:
        user (User): The user to authenticate as when requesting programs.

    Returns:
        list of dict, representing programs returned by the Programs service.
    """
    programs_config = ProgramsApiConfig.current()

    # Bypass caching for staff users, who may be creating Programs and want
    # to see them displayed immediately.
    cache_key = programs_config.CACHE_KEY if programs_config.is_cache_enabled and not user.is_staff else None
    return get_edx_api_data(programs_config, user, 'programs', cache_key=cache_key)


def flatten_programs(programs, course_ids):
    """Flatten the result returned by the Programs API.

    Arguments:
        programs (list): Serialized programs
        course_ids (list): Course IDs to key on.

    Returns:
        dict, programs keyed by course ID
    """
    flattened = {}

    for program in programs:
        try:
            for course_code in program['course_codes']:
                for run in course_code['run_modes']:
                    run_id = run['course_key']
                    if run_id in course_ids:
                        flattened.setdefault(run_id, []).append(program)
        except KeyError:
            log.exception('Unable to parse Programs API response: %r', program)

    return flattened


def get_programs_for_dashboard(user, course_keys):
    """Build a dictionary of programs, keyed by course.

    Given a user and an iterable of course keys, find all the programs relevant
    to the user's dashboard and return them in a dictionary keyed by course key.

    Arguments:
        user (User): The user to authenticate as when requesting programs.
        course_keys (list): List of course keys representing the courses in which
            the given user has active enrollments.

    Returns:
        dict, containing programs keyed by course. Empty if programs cannot be retrieved.
    """
    programs_config = ProgramsApiConfig.current()
    course_programs = {}

    if not programs_config.is_student_dashboard_enabled:
        log.debug('Display of programs on the student dashboard is disabled.')
        return course_programs

    programs = get_programs(user)
    if not programs:
        log.debug('No programs found for the user with ID %d.', user.id)
        return course_programs

    course_ids = [unicode(c) for c in course_keys]
    course_programs = flatten_programs(programs, course_ids)

    return course_programs


def get_programs_for_credentials(user, programs_credentials):
    """ Given a user and an iterable of credentials, get corresponding programs
    data and return it as a list of dictionaries.

    Arguments:
        user (User): The user to authenticate as for requesting programs.
        programs_credentials (list): List of credentials awarded to the user
            for completion of a program.

    Returns:
        list, containing programs dictionaries.
    """
    certificate_programs = []

    programs = get_programs(user)
    if not programs:
        log.debug('No programs for user %d.', user.id)
        return certificate_programs

    for program in programs:
        for credential in programs_credentials:
            if program['id'] == credential['credential']['program_id']:
                program['credential_url'] = credential['certificate_url']
                certificate_programs.append(program)

    return certificate_programs


def get_engaged_programs(user, enrollments):
    """Derive a list of programs in which the given user is engaged.

    Arguments:
        user (User): The user for which to find programs.
        enrollments (list): The user's enrollments.

    Returns:
        list of serialized programs, ordered by most recent enrollment
    """
    programs = get_programs(user)

    enrollments = sorted(enrollments, key=lambda e: e.created, reverse=True)
    # enrollment.course_id is really a course key.
    course_ids = [unicode(e.course_id) for e in enrollments]

    flattened = flatten_programs(programs, course_ids)

    engaged_programs = []
    for course_id in course_ids:
        for program in flattened.get(course_id, []):
            if program not in engaged_programs:
                engaged_programs.append(program)

    return engaged_programs
