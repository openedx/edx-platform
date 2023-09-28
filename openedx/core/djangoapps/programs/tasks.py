"""
This file contains celery tasks for programs-related functionality.
"""
from urllib.parse import urljoin

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey
from requests.exceptions import HTTPError
from xmodule.data import CertificatesDisplayBehaviors

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.api import available_date_for_certificate
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.utils import (
    get_credentials,
    get_credentials_api_base_url,
    get_credentials_api_client,
)
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers

User = get_user_model()

LOGGER = get_task_logger(__name__)
# Maximum number of retries before giving up on awarding credentials.
# For reference, 11 retries with exponential backoff yields a maximum waiting
# time of 2047 seconds (about 30 minutes). Setting this to None could yield
# unwanted behavior: infinite retries.
MAX_RETRIES = 11

PROGRAM_CERTIFICATE = 'program'
COURSE_CERTIFICATE = 'course-run'
DATE_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def get_completed_programs(site, student):
    """
    Given a set of completed courses, determine which programs are completed.

    Args:
        site (Site): Site for which data should be retrieved.
        student (User): Representing the student whose completed programs to check for.

    Returns:
        dict of {program_UUIDs: visible_dates}

    """
    meter = ProgramProgressMeter(site, student)
    return meter.completed_programs_with_available_dates


def get_inverted_programs(student):
    """
    Get programs keyed by course run ID.

    Args:
        student (User): Representing the student whose programs to check for.

    Returns:
        dict, programs keyed by course run ID

    """
    inverted_programs = {}
    for site in Site.objects.all():
        meter = ProgramProgressMeter(site, student)
        inverted_programs.update(meter.invert_programs())

    return inverted_programs


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


def award_program_certificate(client, user, program_uuid, visible_date):
    """
    Issue a new certificate of completion to the given student for the given program.

    Args:
        client:
            credentials API client (requests.Session)
        user:
            The student's user data
        program_uuid:
            uuid of the completed program
        visible_date:
            when the program credential should be visible to user

    Returns:
        None
    """
    credentials_api_base_url = get_credentials_api_base_url()
    api_url = urljoin(f"{credentials_api_base_url}/", "credentials/")
    response = client.post(
        api_url,
        json={
            'username': user.username,
            'lms_user_id': user.id,
            'credential': {
                'type': PROGRAM_CERTIFICATE,
                'program_uuid': program_uuid
            },
            'attributes': [
                {
                    'name': 'visible_date',
                    'value': visible_date.strftime(DATE_FORMAT)
                }
            ]
        }
    )
    response.raise_for_status()


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def award_program_certificates(self, username):  # lint-amnesty, pylint: disable=too-many-statements
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

    If this function is moved, make sure to update it's entry in
    EXPLICIT_QUEUES in the settings files so it runs in the correct queue.

    Args:
        username (str): The username of the student

    Returns:
        None

    """
    def _retry_with_custom_exception(username, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to award program certificate for user {username}. Reason: {reason}"
        )
        return self.retry(
            exc=exception,
            countdown=countdown,
            max_retries=MAX_RETRIES
        )

    LOGGER.info(f"Running task award_program_certificates for username {username}")
    programs_without_certificates = configuration_helpers.get_value('programs_without_certificates', [])
    if programs_without_certificates:
        if str(programs_without_certificates[0]).lower() == "all":
            # this check will prevent unnecessary logging for partners without program certificates
            return

    countdown = 2 ** self.request.retries
    # If the credentials config model is disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.

    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        error_msg = (
            "Task award_program_certificates cannot be executed when credentials issuance is disabled in API config"
        )
        LOGGER.warning(error_msg)
        raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown)

    try:
        try:
            student = User.objects.get(username=username)
        except User.DoesNotExist:
            LOGGER.exception(f"Task award_program_certificates was called with invalid username {username}")
            # Don't retry for this case - just conclude the task.
            return
        completed_programs = {}
        for site in Site.objects.all():
            completed_programs.update(get_completed_programs(site, student))
        if not completed_programs:
            # No reason to continue beyond this point unless/until this
            # task gets updated to support revocation of program certs.
            LOGGER.info(f"Task award_program_certificates was called for user {username} with no completed programs")
            return

        # Determine which program certificates the user has already been awarded, if any.
        existing_program_uuids = get_certified_programs(student)

        # we will skip all the programs which have already been awarded and we want to skip the programs
        # which are exit in site configuration in 'programs_without_certificates' list.
        awarded_and_skipped_program_uuids = list(set(existing_program_uuids + list(programs_without_certificates)))

    except Exception as exc:
        error_msg = f"Failed to determine program certificates to be awarded for user {username}. {exc}"
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown) from exc

    # For each completed program for which the student doesn't already have a
    # certificate, award one now.
    #
    # This logic is important, because we will retry the whole task if awarding any particular program cert fails.
    #
    # N.B. the list is sorted to facilitate deterministic ordering, e.g. for tests.
    new_program_uuids = sorted(list(set(completed_programs.keys()) - set(awarded_and_skipped_program_uuids)))
    if new_program_uuids:
        try:
            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )
        except Exception as exc:
            error_msg = "Failed to create a credentials API client to award program certificates"
            LOGGER.exception(error_msg)
            # Retry because a misconfiguration could be fixed
            raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown) from exc

        failed_program_certificate_award_attempts = []
        for program_uuid in new_program_uuids:
            visible_date = completed_programs[program_uuid]
            try:
                LOGGER.info(f"Visible date for user {username} : program {program_uuid} is {visible_date}")
                award_program_certificate(credentials_client, student, program_uuid, visible_date)
                LOGGER.info(f"Awarded certificate for program {program_uuid} to user {username}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.exception(
                        f"Certificate for program {program_uuid} could not be found. " +
                        f"Unable to award certificate to user {username}. The program might not be configured."
                    )
                elif exc.response.status_code == 429:
                    rate_limit_countdown = 60
                    error_msg = (
                        f"Rate limited. "
                        f"Retrying task to award certificates to user {username} in {rate_limit_countdown} seconds"
                    )
                    LOGGER.info(error_msg)
                    # Retry after 60 seconds, when we should be in a new throttling window
                    raise _retry_with_custom_exception(
                        username=username,
                        reason=error_msg,
                        countdown=rate_limit_countdown
                    ) from exc
                else:
                    LOGGER.exception(
                        f"Unable to award certificate to user {username} for program {program_uuid}. "
                        "The program might not be configured."
                    )
            except Exception:  # pylint: disable=broad-except
                # keep trying to award other certs, but retry the whole task to fix any missing entries
                LOGGER.exception(f"Failed to award certificate for program {program_uuid} to user {username}.")
                failed_program_certificate_award_attempts.append(program_uuid)

        if failed_program_certificate_award_attempts:
            # N.B. This logic assumes that this task is idempotent
            LOGGER.info(f"Retrying task to award failed certificates to user {username}")
            # The error message may change on each reattempt but will never be raised until
            # the max number of retries have been exceeded. It is unlikely that this list
            # will change by the time it reaches its maximimum number of attempts.
            error_msg = (
                f"Failed to award certificate for user {username} "
                f"for programs {failed_program_certificate_award_attempts}"
            )
            raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown)
    else:
        LOGGER.info(f"User {username} is not eligible for any new program certificates")

    LOGGER.info(f"Successfully completed the task award_program_certificates for username {username}")


def post_course_certificate_configuration(client, cert_config, certificate_available_date=None):
    """
    Make a POST request to the Credentials IDA's `course_certificates` endpoint (/api/v2/course_certificates/). This
    endpoint manages the course certificate configurations within the Credentials IDA.

    Args:
        client(Session): An authenticated Credentials API Client
        cert_config(Dict): A dictionary containing course metadata (course-run key and mode as Strings) important to the
            Course Certificate Configuration.
        certificate_available_date(Str): The desired Certificate Available Date for the Course Certificate Configuration
            in the form of an ISO 8601 DateTime String.
    """
    credentials_api_base_url = get_credentials_api_base_url()
    credentials_api_url = urljoin(f"{credentials_api_base_url}/", "course_certificates/")

    response = client.post(
        credentials_api_url,
        json={
            "course_id": cert_config['course_id'],
            "certificate_type": cert_config['mode'],
            "certificate_available_date": certificate_available_date,
            "is_active": True
        }
    )

    # Sometimes helpful error context is swallowed when calling `raise_for_status()`. We try to print out any additional
    # error details here in the hope that it will save someone time when debugging an issue.
    #
    # Also... even though this endpoint does an `update_or_create()` on the Credentials side, it always passes back a
    # 201 on a successful call.
    if response.status_code != 201:
        LOGGER.error(
            "Error creating or updating a course certificate configuration in the Credentials IDA. Additional details: "
            f"{response.text}"
        )
    response.raise_for_status()


def post_course_certificate(client, username, certificate, visible_date, date_override=None, org=None):
    """
    POST a certificate that has been updated to Credentials
    """
    credentials_api_base_url = get_credentials_api_base_url(org)
    api_url = urljoin(f"{credentials_api_base_url}/", "credentials/")

    response = client.post(
        api_url,
        json={
            'username': username,
            'status': 'awarded' if certificate.is_valid() else 'revoked',  # Only need the two options at this time
            'credential': {
                'course_run_key': str(certificate.course_id),
                'mode': certificate.mode,
                'type': COURSE_CERTIFICATE,
            },
            'date_override': {'date': date_override.strftime(DATE_FORMAT)} if date_override else None,
            'attributes': [
                {
                    'name': 'visible_date',
                    'value': visible_date.strftime(DATE_FORMAT)
                }
            ]
        }
    )
    response.raise_for_status()


# pylint: disable=W0613
@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def update_credentials_course_certificate_configuration_available_date(
    self,
    course_key,
    certificate_available_date=None
):
    """
    This task will update the CourseCertificate configuration's available date
    in Credentials. This is different from the "visible_date" attribute. This
    date will always either be the available date that is set in Studio for a
    given course, or it will be None.

    Arguments:
        course_run_key (str): The course run key to award the certificate for
        certificate_available_date (str): A string representation of the
            datetime for when to make the certificate available to the user. If
            not provided, it will be None.
    """
    LOGGER.info(
        f"Running task `update_credentials_course_certificate_configuration_available_date` for course {course_key} "
        f"with certificate_available_date {certificate_available_date}"
    )
    course_key = str(course_key)
    course_modes = CourseMode.objects.filter(course_id=course_key)
    # There should only ever be one certificate relevant mode per course run
    modes = [mode.slug for mode in course_modes if mode.slug in CourseMode.CERTIFICATE_RELEVANT_MODES]
    if len(modes) != 1:
        LOGGER.exception(
            f'Either course {course_key} has no certificate mode or multiple modes. Task failed.'
        )
        return

    credentials_client = get_credentials_api_client(
        User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
    )
    cert_config = {
        'course_id': course_key,
        'mode': modes[0],
    }
    post_course_certificate_configuration(
        client=credentials_client,
        cert_config=cert_config,
        certificate_available_date=certificate_available_date
    )


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def award_course_certificate(self, username, course_run_key):
    """
    This task is designed to be called whenever a student GeneratedCertificate is updated, or when a course-run's
    `certificate_available_date` value is updated.

    It can be called independently for a username and a course_run, but is invoked on each GeneratedCertificate.save.

    If this function is moved, make sure to update it's entry in EXPLICIT_QUEUES in the settings files so it runs in the
    correct queue.

    Arguments:
        username (str): The user to award the Credentials course cert to
        course_run_key (str): The course run key to award the certificate for
    """
    def _retry_with_custom_exception(username, course_run_key, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to award course certificate for user {username} for course {course_run_key}. Reason: {reason}"
        )
        return self.retry(
            exc=exception,
            countdown=countdown,
            max_retries=MAX_RETRIES
        )

    LOGGER.info(f"Running task award_course_certificate for username {username}")

    countdown = 2 ** self.request.retries

    # If the credentials config model is disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        error_msg = (
            "Task award_course_certificate cannot be executed when credentials issuance is disabled in API config"
        )
        LOGGER.warning(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_run_key=course_run_key,
            reason=error_msg,
            countdown=countdown
        )

    try:
        course_key = CourseKey.from_string(course_run_key)
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            LOGGER.exception(f"Task award_course_certificate was called with invalid username {username}")
            # Don't retry for this case - just conclude the task.
            return
        # Get the cert for the course key and username if it's both passing and available in professional/verified
        try:
            certificate = GeneratedCertificate.eligible_certificates.get(
                user=user.id,
                course_id=course_key
            )
        except GeneratedCertificate.DoesNotExist:
            LOGGER.exception(
                "Task award_course_certificate was called without Certificate found "
                f"for {course_key} to user {username}"
            )
            return
        if certificate.mode in CourseMode.CERTIFICATE_RELEVANT_MODES:
            try:
                course_overview = CourseOverview.get_from_id(course_key)
            except (CourseOverview.DoesNotExist, OSError):
                LOGGER.exception(
                    f"Task award_course_certificate was called without course overview data for course {course_key}"
                )
                return

            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )

            visible_date = available_date_for_certificate(
                course_overview,
                certificate,
            )

            LOGGER.info(
                "Task award_course_certificate will award certificate for course "
                f"{course_key} with a visible date of {visible_date}"
            )

            # If the certificate has an associated CertificateDateOverride, send it along
            try:
                date_override = certificate.date_override.date
                LOGGER.info(
                    "Task award_course_certificate will award certificate for course {course_key} with a date override "
                    f"of {date_override}"
                )
            except ObjectDoesNotExist:
                date_override = None

            post_course_certificate(
                credentials_client, username, certificate, visible_date, date_override, org=course_key.org
            )

            LOGGER.info(f"Awarded certificate for course {course_key} to user {username}")
    except Exception as exc:
        error_msg = f"Failed to determine course certificates to be awarded for user {username}."
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_run_key=course_run_key,
            reason=error_msg,
            countdown=countdown
        ) from exc


def get_revokable_program_uuids(course_specific_programs, student):
    """
    Get program uuids for which certificate to be revoked.

    Checks for existing learner certificates and filter out the program UUIDS
    for which a certificate needs to be revoked.

    Args:
        course_specific_programs (dict[]): list of programs specific to a course
        student (User): Representing the student whose programs to check for.

    Returns:
        list if program UUIDs for which certificates to be revoked

    """
    program_uuids_to_revoke = []
    existing_program_uuids = get_certified_programs(student)
    for program in course_specific_programs:
        if program['uuid'] in existing_program_uuids:
            program_uuids_to_revoke.append(program['uuid'])

    return program_uuids_to_revoke


def revoke_program_certificate(client, username, program_uuid):
    """
    Revoke a certificate of the given student for the given program.

    Args:
        client: credentials API client (requests.Session)
        username: The username of the student
        program_uuid: uuid of the program

    Returns:
        None
    """
    credentials_api_base_url = get_credentials_api_base_url()
    api_url = urljoin(f"{credentials_api_base_url}/", "credentials/")
    response = client.post(
        api_url,
        json={
            'username': username,
            'status': 'revoked',
            'credential': {
                'type': PROGRAM_CERTIFICATE,
                'program_uuid': program_uuid
            }
        }
    )
    response.raise_for_status()


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def revoke_program_certificates(self, username, course_key):  # lint-amnesty, pylint: disable=too-many-statements
    """
    This task is designed to be called whenever a student's course certificate is
    revoked.

    It will consult with a variety of APIs to determine whether or not the
    specified user's certificate should be revoked in one or more programs, and
    use the credentials service to revoke the said certificates if so.

    If this function is moved, make sure to update it's entry in
    EXPLICIT_QUEUES in the settings files so it runs in the correct queue.

    Args:
        username (str): The username of the student
        course_key (str): The course identifier

    Returns:
        None

    """
    def _retry_with_custom_exception(username, course_key, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to revoke program certificate for user {username} for course {course_key}. Reason: {reason}"
        )
        return self.retry(
            exc=exception,
            countdown=countdown,
            max_retries=MAX_RETRIES
        )

    countdown = 2 ** self.request.retries
    # If the credentials config model is disabled for this
    # feature, it may indicate a condition where processing of such tasks
    # has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.

    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        error_msg = (
            "Task revoke_program_certificates cannot be executed when credentials issuance is disabled in API config"
        )
        LOGGER.warning(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_key=course_key,
            reason=error_msg,
            countdown=countdown
        )

    try:
        student = User.objects.get(username=username)
    except User.DoesNotExist:
        LOGGER.exception(f"Task revoke_program_certificates was called with invalid username {username}", username)
        # Don't retry for this case - just conclude the task.
        return

    try:
        inverted_programs = get_inverted_programs(student)
        course_specific_programs = inverted_programs.get(course_key)
        if not course_specific_programs:
            # No reason to continue beyond this point
            LOGGER.info(
                f"Task revoke_program_certificates was called for user {username} "
                f"and course {course_key} with no engaged programs"
            )
            return

        # Determine which program certificates the user has already been awarded, if any.
        program_uuids_to_revoke = get_revokable_program_uuids(course_specific_programs, student)
    except Exception as exc:
        error_msg = (
            f"Failed to determine program certificates to be revoked for user {username} "
            f"with course {course_key}"
        )
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_key=course_key,
            reason=error_msg,
            countdown=countdown
        ) from exc

    if program_uuids_to_revoke:
        try:
            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )
        except Exception as exc:
            error_msg = "Failed to create a credentials API client to revoke program certificates"
            LOGGER.exception(error_msg)
            # Retry because a misconfiguration could be fixed
            raise _retry_with_custom_exception(username, course_key, reason=exc, countdown=countdown) from exc

        failed_program_certificate_revoke_attempts = []
        for program_uuid in program_uuids_to_revoke:
            try:
                revoke_program_certificate(credentials_client, username, program_uuid)
                LOGGER.info(f"Revoked certificate for program {program_uuid} for user {username}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.exception(
                        f"Certificate for program {program_uuid} could not be found. "
                        f"Unable to revoke certificate for user {username}"
                    )
                elif exc.response.status_code == 429:
                    rate_limit_countdown = 60
                    error_msg = (
                        "Rate limited. Retrying task to revoke certificates "
                        f"for user {username} in {rate_limit_countdown} seconds"
                    )
                    LOGGER.info(error_msg)
                    # Retry after 60 seconds, when we should be in a new throttling window
                    raise _retry_with_custom_exception(
                        username,
                        course_key,
                        reason=error_msg,
                        countdown=rate_limit_countdown
                    ) from exc
                else:
                    LOGGER.exception(
                        f"Unable to revoke certificate for user {username} for program {program_uuid}."
                    )
            except Exception:  # pylint: disable=broad-except
                # keep trying to revoke other certs, but retry the whole task to fix any missing entries
                LOGGER.warning(f"Failed to revoke certificate for program {program_uuid} of user {username}.")
                failed_program_certificate_revoke_attempts.append(program_uuid)

        if failed_program_certificate_revoke_attempts:
            # N.B. This logic assumes that this task is idempotent
            LOGGER.info(f"Retrying task to revoke failed certificates to user {username}")
            # The error message may change on each reattempt but will never be raised until
            # the max number of retries have been exceeded. It is unlikely that this list
            # will change by the time it reaches its maximimum number of attempts.
            error_msg = (
                f"Failed to revoke certificate for user {username} "
                f"for programs {failed_program_certificate_revoke_attempts}"
            )
            raise _retry_with_custom_exception(
                username,
                course_key,
                reason=error_msg,
                countdown=countdown
            )

    else:
        LOGGER.info(f"There is no program certificates for user {username} to revoke")
    LOGGER.info(f"Successfully completed the task revoke_program_certificates for username {username}")


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def update_certificate_visible_date_on_course_update(self, course_key):
    """
    This task is designed to be called whenever a course-run's `certificate_available_date` is updated.

    When executed, this task will first get a list of all learners within the course-run that have earned a certificate.
    Next, we will enqueue an additional `award_course_certificate` task for each learner in this list. These subtasks
    will be responsible for updating the `visible_date` attribute on each certificate the Credentials IDA knows about.

    If this function is moved, make sure to update it's entry in EXPLICIT_QUEUES in the settings files so it runs in the
    correct queue.

    Arguments:
        course_key(str): The course identifier
    """
    countdown = 2 ** self.request.retries

    # If the CredentialsApiConfig configuration model is disabled for this feature, it may indicate a condition where
    # processing of such tasks has been temporarily disabled. Since this is a recoverable situation, mark this task for
    # retry instead of failing it.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        error_msg = (
            "Cannot execute the `update_certificate_visible_date_on_course_update` task. Issuing user credentials "
            "through the Credentials IDA is disabled."
        )
        LOGGER.warning(error_msg)
        exception = MaxRetriesExceededError(
            f"Failed to update the `visible_date` attribute for certificates in course {course_key}. Reason: "
            f"{error_msg}"
        )
        raise self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)

    # Retrieve a list of all usernames of learners who have a certificate record in this course-run. The
    # Credentials IDA REST API still requires a username as the main identifier for the learner.
    users_with_certificates_in_course = (
        GeneratedCertificate
        .eligible_available_certificates
        .filter(course_id=course_key)
        .values_list('user__username', flat=True)
    )

    LOGGER.info(
        f"Resending course certificates for learners in course {course_key} to the Credentials service. Queueing "
        f"{len(users_with_certificates_in_course)} `award_course_certificate` tasks."
    )
    for user in users_with_certificates_in_course:
        award_course_certificate.delay(user, str(course_key))


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def update_certificate_available_date_on_course_update(self, course_key):
    """
    This task is designed to be called whenever a course-run's `certificate_available_date` is updated.

    When executed, this task will determine if we need to enqueue an
    `update_credentials_course_certificate_configuration_available_date` task associated with the specified course-run
    key from this task. If so, this subtask is responsible for making a REST API call to the Credentials IDA to update
    the specified course-run's Course Certificate configuration with the new `certificate_available_date` value.

    Args:
        course_key(str): The course identifier
    """
    countdown = 2 ** self.request.retries

    # If the CredentialsApiConfig configuration model is disabled for this feature, it may indicate a condition where
    # processing of such tasks has been temporarily disabled. Since this is a recoverable situation, mark this task for
    # retry instead of failing it.
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        error_msg = (
            "Cannot execute the `update_certificate_visible_date_on_course_update` task. Issuing user credentials "
            "through the Credentials IDA is disabled."
        )
        LOGGER.warning(error_msg)
        exception = MaxRetriesExceededError(
            "Failed to update the `certificate_available_date` in the Credentials service for course-run "
            f"{course_key}. Reason: {error_msg}"
        )
        raise self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)

    course_overview = CourseOverview.get_from_id(course_key)
    # Update the Credentials service's CourseCertificate configuration with the new `certificate_available_date` if:
    #   - The course-run is instructor-paced, AND
    #   - The `certificates_display_behavior` is set to "end_with_date",
    if (
        course_overview and
        course_overview.self_paced is False and
        course_overview.certificates_display_behavior == CertificatesDisplayBehaviors.END_WITH_DATE
    ):
        LOGGER.info(
            f"Queueing task to update the `certificate_available_date` of course-run {course_key} to "
            f"[{course_overview.certificate_available_date}] in the Credentials service"
        )
        update_credentials_course_certificate_configuration_available_date.delay(
            str(course_key),
            str(course_overview.certificate_available_date)
        )
    # OR,
    #   - The course-run is self-paced, AND
    #   - The `certificate_available_date` is (now) None. (This task will be executed after an update to the course
    #     overview)
    # There are times when the CourseCertificate configuration of a self-paced course-run in Credentials can become
    # associated with a `certificate_available_date`. This ends up causing learners' certificate to be incorrectly
    # hidden. This is due to the Credentials IDA not understanding the concept of course pacing. Thus, we need a way
    # to remove this value from self-paced courses in Credentials.
    elif (
        course_overview and
        course_overview.self_paced is True and
        course_overview.certificate_available_date is None
    ):
        LOGGER.info(
            "Queueing task to remove the `certificate_available_date` in the Credentials service for course-run "
            f"{course_key}"
        )
        update_credentials_course_certificate_configuration_available_date.delay(str(course_key), None)
    # ELSE, we don't meet the criteria to update the course cert config in the Credentials IDA
    else:
        LOGGER.warning(
            f"Skipping update of the `certificate_available_date` for course {course_key} in the Credentials service. "
            "This course-run does not meet the required criteria for an update."
        )
