"""
This file contains celery tasks for programs-related functionality.
"""
from celery import task
from celery.utils.log import get_task_logger  # pylint: disable=no-name-in-module, import-error
from django.conf import settings
from django.contrib.auth.models import User
from edx_rest_api_client.client import EdxRestApiClient

from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.utils import get_user_credentials
from openedx.core.djangoapps.programs.models import ProgramsApiConfig
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
from openedx.core.lib.token_utils import get_id_token


LOGGER = get_task_logger(__name__)
# Under cms the following setting is not defined, leading to errors during tests.
ROUTING_KEY = getattr(settings, 'CREDENTIALS_GENERATION_ROUTING_KEY', None)


def get_api_client(api_config, student):
    """
    Create and configure an API client for authenticated HTTP requests.

    Args:
        api_config: ProgramsApiConfig or CredentialsApiConfig object
        student: User object as whom to authenticate to the API

    Returns:
        EdxRestApiClient

    """
    id_token = get_id_token(student, api_config.OAUTH2_CLIENT_NAME)
    return EdxRestApiClient(api_config.internal_api_url, jwt=id_token)


def get_completed_programs(student):
    """
    Given a set of completed courses, determine which programs are completed.

    Args:
        student (User): Representing the student whose completed programs to check for.

    Returns:
        list of program ids

    """
    meter = ProgramProgressMeter(student)

    return meter.completed_programs


def get_awarded_certificate_programs(student):
    """
    Find the ids of all the programs for which the student has already been awarded
    a certificate.

    Args:
        student:
            User object representing the student

    Returns:
        ids of the programs for which the student has been awarded a certificate

    """
    return [
        credential['credential']['program_id']
        for credential in get_user_credentials(student)
        if 'program_id' in credential['credential'] and credential['status'] == 'awarded'
    ]


def award_program_certificate(client, username, program_id):
    """
    Issue a new certificate of completion to the given student for the given program.

    Args:
        client:
            credentials API client (EdxRestApiClient)
        username:
            The username of the student
        program_id:
            id of the completed program

    Returns:
        None

    """
    client.user_credentials.post({
        'username': username,
        'credential': {'program_id': program_id},
        'attributes': []
    })


@task(bind=True, ignore_result=True, routing_key=ROUTING_KEY)
def award_program_certificates(self, username):
    """
    This task is designed to be called whenever a student's completion status
    changes with respect to one or more courses (primarily, when a course
    certificate is awarded).

    It will consult with a variety of APIs to determine whether or not the
    specified user should be awarded a certificate in one or more programs, and
    use the credentials service to create said certificates if so.

    This task may also be invoked independently of any course completion status
    change - for example, to backpopulate missing program credentials for a
    student.

    Args:
        username:
            The username of the student

    Returns:
        None

    """
    LOGGER.info('Running task award_program_certificates for username %s', username)

    config = ProgramsApiConfig.current()
    countdown = 2 ** self.request.retries

    # If either programs or credentials config models are disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.
    if not config.is_certification_enabled:
        LOGGER.warning(
            'Task award_program_certificates cannot be executed when program certification is disabled in API config',
        )
        raise self.retry(countdown=countdown, max_retries=config.max_retries)

    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        LOGGER.warning(
            'Task award_program_certificates cannot be executed when credentials issuance is disabled in API config',
        )
        raise self.retry(countdown=countdown, max_retries=config.max_retries)

    try:
        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            LOGGER.exception('Task award_program_certificates was called with invalid username %s', username)
            # Don't retry for this case - just conclude the task.
            return

        program_ids = get_completed_programs(student)
        if not program_ids:
            # No reason to continue beyond this point unless/until this
            # task gets updated to support revocation of program certs.
            LOGGER.info('Task award_program_certificates was called for user %s with no completed programs', username)
            return

        # Determine which program certificates the user has already been
        # awarded, if any.
        existing_program_ids = get_awarded_certificate_programs(student)

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception('Failed to determine program certificates to be awarded for user %s', username)
        raise self.retry(exc=exc, countdown=countdown, max_retries=config.max_retries)

    # For each completed program for which the student doesn't already have a
    # certificate, award one now.
    #
    # This logic is important, because we will retry the whole task if awarding any particular program cert fails.
    #
    # N.B. the list is sorted to facilitate deterministic ordering, e.g. for tests.
    new_program_ids = sorted(list(set(program_ids) - set(existing_program_ids)))
    if new_program_ids:
        try:
            credentials_client = get_api_client(
                CredentialsApiConfig.current(),
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME)  # pylint: disable=no-member
            )
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception('Failed to create a credentials API client to award program certificates')
            # Retry because a misconfiguration could be fixed
            raise self.retry(exc=exc, countdown=countdown, max_retries=config.max_retries)

        retry = False
        for program_id in new_program_ids:
            try:
                award_program_certificate(credentials_client, username, program_id)
                LOGGER.info('Awarded certificate for program %s to user %s', program_id, username)
            except Exception:  # pylint: disable=broad-except
                # keep trying to award other certs, but retry the whole task to fix any missing entries
                LOGGER.exception('Failed to award certificate for program %s to user %s', program_id, username)
                retry = True

        if retry:
            # N.B. This logic assumes that this task is idempotent
            LOGGER.info('Retrying task to award failed certificates to user %s', username)
            raise self.retry(countdown=countdown, max_retries=config.max_retries)
    else:
        LOGGER.info('User %s is not eligible for any new program certificates', username)

    LOGGER.info('Successfully completed the task award_program_certificates for username %s', username)
