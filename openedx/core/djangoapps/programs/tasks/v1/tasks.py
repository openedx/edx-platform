"""
This file contains celery tasks for programs-related functionality.
"""
from celery import task
from celery.utils.log import get_task_logger  # pylint: disable=no-name-in-module, import-error
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from edx_rest_api_client import exceptions

from course_modes.models import CourseMode
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.certificates.api import display_date_for_certificate
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.utils import get_credentials, get_credentials_api_client
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter


LOGGER = get_task_logger(__name__)
# Under cms the following setting is not defined, leading to errors during tests.
ROUTING_KEY = getattr(settings, 'CREDENTIALS_GENERATION_ROUTING_KEY', None)
# Maximum number of retries before giving up on awarding credentials.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11

PROGRAM_CERTIFICATE = 'program'
COURSE_CERTIFICATE = 'course-run'


def get_completed_programs(site, student):
    """
    Given a set of completed courses, determine which programs are completed.

    Args:
        site (Site): Site for which data should be retrieved.
        student (User): Representing the student whose completed programs to check for.

    Returns:
        list of program UUIDs

    """
    meter = ProgramProgressMeter(site, student)
    return meter.completed_programs


def get_certified_programs(student):
    """
    Find the UUIDs of all the programs for which the student has already been awarded
    a certificate.

    Args:
        student:
            User object representing the student

    Returns:
        str[]: UUIDs of the programs for which the student has been awarded a certificate

    """
    certified_programs = []
    for credential in get_credentials(student, credential_type='program'):
        certified_programs.append(credential['credential']['program_uuid'])
    return certified_programs


def award_program_certificate(client, username, program_uuid):
    """
    Issue a new certificate of completion to the given student for the given program.

    Args:
        client:
            credentials API client (EdxRestApiClient)
        username:
            The username of the student
        program_uuid:
            uuid of the completed program

    Returns:
        None

    """
    client.credentials.post({
        'username': username,
        'credential': {
            'type': PROGRAM_CERTIFICATE,
            'program_uuid': program_uuid
        },
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
        username (str): The username of the student

    Returns:
        None

    """
    LOGGER.info('Running task award_program_certificates for username %s', username)

    countdown = 2 ** self.request.retries

    # If the credentials config model is disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.

    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        LOGGER.warning(
            'Task award_program_certificates cannot be executed when credentials issuance is disabled in API config',
        )
        raise self.retry(countdown=countdown, max_retries=MAX_RETRIES)

    try:
        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            LOGGER.exception('Task award_program_certificates was called with invalid username %s', username)
            # Don't retry for this case - just conclude the task.
            return
        program_uuids = []
        for site in Site.objects.all():
            program_uuids.extend(get_completed_programs(site, student))
        if not program_uuids:
            # No reason to continue beyond this point unless/until this
            # task gets updated to support revocation of program certs.
            LOGGER.info('Task award_program_certificates was called for user %s with no completed programs', username)
            return

        # Determine which program certificates the user has already been awarded, if any.
        existing_program_uuids = get_certified_programs(student)

    except Exception as exc:  # pylint: disable=broad-except
        LOGGER.exception('Failed to determine program certificates to be awarded for user %s', username)
        raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)

    # For each completed program for which the student doesn't already have a
    # certificate, award one now.
    #
    # This logic is important, because we will retry the whole task if awarding any particular program cert fails.
    #
    # N.B. the list is sorted to facilitate deterministic ordering, e.g. for tests.
    new_program_uuids = sorted(list(set(program_uuids) - set(existing_program_uuids)))
    if new_program_uuids:
        try:
            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception('Failed to create a credentials API client to award program certificates')
            # Retry because a misconfiguration could be fixed
            raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)

        retry = False
        for program_uuid in new_program_uuids:
            try:
                award_program_certificate(credentials_client, username, program_uuid)
                LOGGER.info('Awarded certificate for program %s to user %s', program_uuid, username)
            except exceptions.HttpNotFoundError:
                LOGGER.exception(
                    'Certificate for program %s not configured, unable to award certificate to %s',
                    program_uuid, username
                )
            except Exception:  # pylint: disable=broad-except
                # keep trying to award other certs, but retry the whole task to fix any missing entries
                LOGGER.warning('Failed to award certificate for program {uuid} to user {username}.'.format(
                    uuid=program_uuid, username=username))
                retry = True

        if retry:
            # N.B. This logic assumes that this task is idempotent
            LOGGER.info('Retrying task to award failed certificates to user %s', username)
            raise self.retry(countdown=countdown, max_retries=MAX_RETRIES)
    else:
        LOGGER.info('User %s is not eligible for any new program certificates', username)

    LOGGER.info('Successfully completed the task award_program_certificates for username %s', username)


def post_course_certificate(client, username, certificate, visible_date):
    """
    POST a certificate that has been updated to Credentials
    """
    client.credentials.post({
        'username': username,
        'status': 'awarded' if certificate.is_valid() else 'revoked',  # Only need the two options at this time
        'credential': {
            'course_run_key': str(certificate.course_id),
            'mode': certificate.mode,
            'type': COURSE_CERTIFICATE,
        },
        'attributes': [
            {
                'name': 'visible_date',
                'value': visible_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            }
        ]
    })


@task(bind=True, ignore_result=True, routing_key=ROUTING_KEY)
def award_course_certificate(self, username, course_run_key):
    """
    This task is designed to be called whenever a student GeneratedCertificate is updated.
    It can be called independently for a username and a course_run, but is invoked on each GeneratedCertificate.save.
    """

    LOGGER.info('Running task award_course_certificate for username %s', username)

    countdown = 2 ** self.request.retries

    # If the credentials config model is disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.

    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        LOGGER.warning(
            'Task award_course_certificate cannot be executed when credentials issuance is disabled in API config',
        )
        raise self.retry(countdown=countdown, max_retries=MAX_RETRIES)

    try:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            LOGGER.exception('Task award_course_certificate was called with invalid username %s', username)
            # Don't retry for this case - just conclude the task.
            return
        # Get the cert for the course key and username if it's both passing and available in professional/verified
        try:
            certificate = GeneratedCertificate.eligible_certificates.get(
                user=user.id,
                course_id=course_run_key
            )
        except GeneratedCertificate.DoesNotExist:
            LOGGER.exception(
                'Task award_course_certificate was called without Certificate found for %s to user %s',
                course_run_key,
                username
            )
            return
        if certificate.mode in CourseMode.VERIFIED_MODES + CourseMode.CREDIT_MODES:
            try:
                course_overview = CourseOverview.get_from_id(course_run_key)
            except (CourseOverview.DoesNotExist, IOError):
                LOGGER.exception(
                    'Task award_course_certificate was called without course overview data for course %s',
                    course_run_key
                )
                return
            credentials_client = get_credentials_api_client(User.objects.get(
                username=settings.CREDENTIALS_SERVICE_USERNAME),
                org=course_run_key.org,
            )
            # FIXME This may result in visible dates that do not update alongside the Course Overview if that changes
            # This is a known limitation of this implementation and was chosen to reduce the amount of replication,
            # endpoints, celery tasks, and jenkins jobs that needed to be written for this functionality
            visible_date = display_date_for_certificate(course_overview, certificate)
            post_course_certificate(credentials_client, username, certificate, visible_date)

            LOGGER.info('Awarded certificate for course %s to user %s', course_run_key, username)
    except Exception as exc:
        LOGGER.exception('Failed to determine course certificates to be awarded for user %s', username)
        raise self.retry(exc=exc, countdown=countdown, max_retries=MAX_RETRIES)
