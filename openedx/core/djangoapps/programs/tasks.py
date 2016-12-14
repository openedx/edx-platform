"""
This file contains celery tasks for programs-related functionality.
"""

from celery import task
from celery.utils.log import get_task_logger  # pylint: disable=no-name-in-module, import-error

from lms.djangoapps.certificates.api import get_certificates_for_user

LOGGER = get_task_logger(__name__)


@task
def award_program_certificates(username):
    """
    This task is designed to be called whenever a user's completion status
    changes with respect to one or more courses (primarily, when a course
    certificate is awarded).

    It will consult with a variety of APIs to determine whether or not the
    specified user should be awarded a certificate in one or more programs, and
    use the credentials service to create said certificates if so.

    This task may also be invoked independently of any course completion status
    change - for example, to backpopulate missing program credentials for a
    user.

    TODO: this is shelled out and incomplete for now.
    """

    # fetch the set of all course runs for which the user has earned a certificate
    LOGGER.debug('fetching all completed courses for user %s', username)
    user_certs = get_certificates_for_user(username)
    course_certs = [
        {'course_id': uc['course_id'], 'mode': uc['mode']}
        for uc in user_certs
        if uc['status'] in ('downloadable', 'generating')
    ]

    # invoke the Programs API completion check endpoint to identify any programs
    # that are satisfied by these course completions
    LOGGER.debug('determining completed programs for courses: %r', course_certs)
    program_ids = []  # TODO

    # determine which program certificates the user has already been awarded, if
    # any, and remove those, since they already exist.
    LOGGER.debug('fetching existing program certificates for %s', username)
    existing_program_ids = []  # TODO
    new_program_ids = list(set(program_ids) - set(existing_program_ids))

    # generate a new certificate for each of the remaining programs.
    LOGGER.debug('generating new program certificates for %s in programs: %r', username, new_program_ids)
    for program_id in new_program_ids:
        LOGGER.debug('calling credentials service to issue certificate for user %s in program %s', username, program_id)
        # TODO
