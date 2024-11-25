"""
This file contains celery tasks and utility functions responsible for syncing course and program certificate metadata
between the monolith and the Credentials IDA.
"""
<<<<<<< HEAD
from typing import Dict, List
=======

from typing import TYPE_CHECKING, Dict, List, Optional
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from urllib.parse import urljoin

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from edx_django_utils.monitoring import set_code_owner_attribute
<<<<<<< HEAD
=======
from opaque_keys import InvalidKeyError
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from opaque_keys.edx.keys import CourseKey
from requests.exceptions import HTTPError

from common.djangoapps.course_modes.models import CourseMode
<<<<<<< HEAD
from lms.djangoapps.certificates.api import available_date_for_certificate
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
from lms.djangoapps.certificates.models import GeneratedCertificate
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview_or_none
from openedx.core.djangoapps.credentials.api import is_credentials_enabled
from openedx.core.djangoapps.credentials.utils import (
    get_credentials,
    get_credentials_api_base_url,
    get_credentials_api_client,
)
from openedx.core.djangoapps.programs.utils import ProgramProgressMeter
from openedx.core.djangoapps.site_configuration import helpers as configuration_helpers
from xmodule.data import CertificatesDisplayBehaviors

<<<<<<< HEAD
=======
if TYPE_CHECKING:
    from datetime import datetime

    from django.contrib.auth.models import User as UserType  # pylint: disable=imported-auth-user
    from requests import Session

>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
User = get_user_model()

LOGGER = get_task_logger(__name__)
# Maximum number of retries before giving up on awarding credentials. For reference, 11 retries with exponential backoff
# yields a maximum waiting time of 2047 seconds (about 30 minutes). Setting this to None could yield unwanted behavior:
# infinite retries.
MAX_RETRIES = 11
PROGRAM_CERTIFICATE = "program"
COURSE_CERTIFICATE = "course-run"
DATE_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


<<<<<<< HEAD
def get_completed_programs(site, student):
=======
def get_completed_programs(site: Site, student: "UserType") -> Dict:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    Given a set of completed courses, determine which programs are completed.

    Args:
        site (Site): Site for which data should be retrieved.
        student (User): Representing the student whose completed programs to check for.

    Returns:
<<<<<<< HEAD
        dict of {program_UUIDs: visible_dates}
=======
        Dict of program_UUIDs:availability dates
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    """
    meter = ProgramProgressMeter(site, student)
    return meter.completed_programs_with_available_dates


<<<<<<< HEAD
def get_inverted_programs(student):
=======
def get_inverted_programs(student: "UserType"):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
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


<<<<<<< HEAD
def get_certified_programs(student: User, raise_on_error: bool = False) -> List[str]:
=======
def get_certified_programs(student: "UserType", raise_on_error: bool = False) -> List[str]:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    Find the UUIDs of all the programs for which the student has already been awarded
    a certificate.

    Args:
        student: User object representing the student

    Keyword Arguments:
        raise_on_error (bool): Reraise errors back to the caller, instead of returning empty results.

    Returns:
        str[]: UUIDs of the programs for which the student has been awarded a certificate

    """
    certified_programs = []
    for credential in get_credentials(
        student,
        credential_type=PROGRAM_CERTIFICATE,
        raise_on_error=raise_on_error,
    ):
        certified_programs.append(credential["credential"]["program_uuid"])
    return certified_programs


<<<<<<< HEAD
def get_revokable_program_uuids(course_specific_programs: List[Dict], student: User) -> List[str]:
=======
def get_revokable_program_uuids(course_specific_programs: List[Dict], student: "UserType") -> List[str]:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    Get program uuids for which certificate to be revoked.

    Checks for existing learner certificates and filter out the program UUIDS
    for which a certificate needs to be revoked.

    Args:
        course_specific_programs (dict[]): list of programs specific to a course
        student (User): Representing the student whose programs to check for.

    Returns:
        list of program UUIDs for which certificates to be revoked

    Raises:
        HttpError, if the API call generated by get_certified_programs fails
    """
    program_uuids_to_revoke = []
    # Get any programs where the user has already been rewarded a certificate
    # Failed API calls with get_certified_programs should raise exceptions,
    # because an empty response would dangerously imply a false negative.
    existing_program_uuids = get_certified_programs(student, raise_on_error=True)
    for program in course_specific_programs:
        if program["uuid"] in existing_program_uuids:
            program_uuids_to_revoke.append(program["uuid"])

    return program_uuids_to_revoke


<<<<<<< HEAD
def award_program_certificate(client, user, program_uuid, visible_date):
=======
def award_program_certificate(client: "Session", user: "UserType", program_uuid: "str") -> None:
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    Issue a new certificate of completion to the given student for the given program.

    Args:
        client:
            credentials API client (requests.Session)
        user:
            The student's user data
        program_uuid:
            uuid of the completed program
<<<<<<< HEAD
        visible_date:
            when the program credential should be visible to user
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    Returns:
        None
    """
    credentials_api_base_url = get_credentials_api_base_url()
    api_url = urljoin(f"{credentials_api_base_url}/", "credentials/")
    response = client.post(
        api_url,
        json={
            "username": user.username,
            "lms_user_id": user.id,
            "credential": {"type": PROGRAM_CERTIFICATE, "program_uuid": program_uuid},
<<<<<<< HEAD
            "attributes": [{"name": "visible_date", "value": visible_date.strftime(DATE_FORMAT)}],
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        },
    )
    response.raise_for_status()


def revoke_program_certificate(client, username, program_uuid):
    """
    Make a request to the Credentials IDA, requesting the system to revoke a program certificate from the given user in
    a given program.

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
            "username": username,
            "status": "revoked",
            "credential": {"type": PROGRAM_CERTIFICATE, "program_uuid": program_uuid},
        },
    )
    response.raise_for_status()


<<<<<<< HEAD
def post_course_certificate(client, username, certificate, visible_date, date_override=None, org=None):
=======
def post_course_certificate(
    client: "Session",
    username: str,
    certificate: GeneratedCertificate,
    date_override: Optional["datetime"] = None,
    org: Optional[str] = None,
):
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    """
    POST a certificate that has been updated to Credentials
    """
    credentials_api_base_url = get_credentials_api_base_url(org)
    api_url = urljoin(f"{credentials_api_base_url}/", "credentials/")

    response = client.post(
        api_url,
        json={
            "username": username,
            "status": "awarded" if certificate.is_valid() else "revoked",  # Only need the two options at this time
            "credential": {
                "course_run_key": str(certificate.course_id),
                "mode": certificate.mode,
                "type": COURSE_CERTIFICATE,
            },
            "date_override": {"date": date_override.strftime(DATE_FORMAT)} if date_override else None,
<<<<<<< HEAD
            "attributes": [{"name": "visible_date", "value": visible_date.strftime(DATE_FORMAT)}],
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        },
    )
    response.raise_for_status()


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
<<<<<<< HEAD

    response = client.post(
        credentials_api_url,
        json={
            "course_id": cert_config["course_id"],
            "certificate_type": cert_config["mode"],
            "certificate_available_date": certificate_available_date,
            "is_active": True,
        },
=======
    certificate_config = {
        "course_id": cert_config["course_id"],
        "certificate_type": cert_config["mode"],
        "certificate_available_date": certificate_available_date,
        "is_active": True,
    }

    response = client.post(
        credentials_api_url,
        json=certificate_config,
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    )

    # Sometimes helpful error context is swallowed when calling `raise_for_status()`. We try to print out any additional
    # error details here in the hope that it will save someone time when debugging an issue.
    #
    # Also... even though this endpoint does an `update_or_create()` on the Credentials side, it always passes back a
    # 201 on a successful call.
    if response.status_code != 201:
        LOGGER.error(
<<<<<<< HEAD
            "Error creating or updating a course certificate configuration in the Credentials IDA. Additional details: "
            f"{response.text}"
=======
            "Error creating or updating a course certificate configuration in the Credentials IDA.\n"
            f"config sent: {certificate_config}\nAdditional details: {response.text}"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        )
    response.raise_for_status()


<<<<<<< HEAD
@shared_task(bind=True, ignore_result=True)
=======
# pylint: disable=unused-argument
@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    max_retries=10,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@set_code_owner_attribute
def award_program_certificates(self, username):  # lint-amnesty, pylint: disable=too-many-statements
    """
    This task is designed to be called whenever a student's completion status changes with respect to one or more
    courses (primarily, when a course certificate is awarded).

    It will consult with a variety of APIs to determine whether or not the specified user should be awarded a program
    certificate in one or more programs, and use the credentials service to create said certificates if so.

    This task may also be invoked independently of any course completion status change - for example, to backpopulate
    missing program credentials for a student.

    If this function is moved, make sure to update it's entry in EXPLICIT_QUEUES in the settings files so it runs in the
    correct queue.

    Args:
        username (str): The username of the student

    Returns:
        None
    """
<<<<<<< HEAD
    def _retry_with_custom_exception(username, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to award a program certificate to user {username}. Reason: {reason}"
        )
        return self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)

    countdown = 2**self.request.retries

    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  Since this is a recoverable situation, mark this task for retry instead of
    # failing it altogether.
=======
    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  This is a recoverable situation, so let celery retry.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    if not is_credentials_enabled():
        error_msg = (
            "Task award_program_certificates cannot be executed, use of the Credentials service is disabled by config"
        )
        LOGGER.warning(error_msg)
<<<<<<< HEAD
        raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown)
=======
        raise MaxRetriesExceededError(f"Failed to award a program certificate. Reason: {error_msg}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    try:
        student = User.objects.get(username=username)
    except User.DoesNotExist:
        LOGGER.warning(
            "Task award_program_certificates was called with an invalid username. Could not retrieve a User instance "
            f"with username {username}"
        )
        return

    # this check will prevent unnecessary logging for partners without program certificates
    programs_without_certificates = configuration_helpers.get_value("programs_without_certificates", [])
    if programs_without_certificates:
        if str(programs_without_certificates[0]).lower() == "all":
            return

<<<<<<< HEAD
    LOGGER.info(f"Running task award_program_certificates for user {student}")
=======
    LOGGER.info(f"Running task award_program_certificates for user {student.id}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    try:
        completed_programs = {}
        for site in Site.objects.all():
            completed_programs.update(get_completed_programs(site, student))

        if not completed_programs:
<<<<<<< HEAD
            LOGGER.warning(f"Task award_program_certificates was called for user {student} with no completed programs")
=======
            LOGGER.warning(
                f"Task award_program_certificates was called for user {student.id} with no completed programs"
            )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            return

        # determine which program certificates have been awarded to the user
        existing_program_uuids = get_certified_programs(student)
        # construct a list of program UUIDs where the learner has already been awarded a program certificate or if the
        # program is part of the "programs without certificates" list in our site configuration
        awarded_and_skipped_program_uuids = list(set(existing_program_uuids + list(programs_without_certificates)))
    except Exception as exc:
<<<<<<< HEAD
        error_msg = f"Failed to determine program certificates to be awarded for user {student}: {exc}"
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown) from exc
=======
        error_msg = f"Failed to determine program certificates to be awarded for user {student.id}: {exc}"
        LOGGER.exception(error_msg)
        raise MaxRetriesExceededError(
            f"Failed to award a program certificate to user {student.id}. Reason: {error_msg}"
        ) from exc
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    # For each completed program for which the student doesn't already have a certificate, award one now.
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
<<<<<<< HEAD
            # Retry because a misconfiguration could be fixed
            raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown) from exc

        failed_program_certificate_award_attempts = []
        for program_uuid in new_program_uuids:
            visible_date = completed_programs[program_uuid]
            try:
                LOGGER.info(
                    f"Visible date for program certificate awarded to user {student} in program {program_uuid} is "
                    f"{visible_date}"
                )
                award_program_certificate(credentials_client, student, program_uuid, visible_date)
                LOGGER.info(f"Awarded program certificate to user {student} in program {program_uuid}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.warning(
                        f"Unable to award a program certificate to user {student} in program {program_uuid}. A "
=======
            # A misconfiguration could be fixed; let celery retry.
            raise MaxRetriesExceededError(
                f"Failed to award a program certificate to user {student.id}. Reason: {error_msg}"
            ) from exc

        failed_program_certificate_award_attempts = []
        for program_uuid in new_program_uuids:
            try:
                award_program_certificate(credentials_client, student, program_uuid)
                LOGGER.info(f"Awarded program certificate to user {student.id} in program {program_uuid}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.warning(
                        f"Unable to award a program certificate to user {student.id} in program {program_uuid}. A "
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                        f"certificate configuration for program {program_uuid} could not be found, the program might "
                        "not be configured correctly in Credentials"
                    )
                elif exc.response.status_code == 429:
<<<<<<< HEAD
                    rate_limit_countdown = 60
                    error_msg = (
                        f"Rate limited. Retrying task to award certificate to user {student} in program "
                        f"{program_uuid} in {rate_limit_countdown} seconds"
                    )
                    LOGGER.warning(error_msg)
                    # Retry after 60 seconds, when we should be in a new throttling window
                    raise _retry_with_custom_exception(
                        username=username,
                        reason=error_msg,
                        countdown=rate_limit_countdown,
                    ) from exc
                else:
                    LOGGER.warning(
                        f"Unable to award program certificate to user {student} in program {program_uuid}. The program "
                        "might not be configured correctly in Credentials"
                    )
            except Exception as exc:  # pylint: disable=broad-except
                # keep trying to award other certs, but retry the whole task to fix any missing entries
                LOGGER.exception(
                    f"Failed to award program certificate to user {student} in program {program_uuid}: {exc}"
=======
                    # Let celery handle retry attempts and backoff
                    error_msg = (
                        f"Rate limited. Attempting to award certificate to user {student.id} in program {program_uuid}."
                    )
                    LOGGER.warning(error_msg)
                    raise MaxRetriesExceededError(
                        f"Failed to award a program certificate to user {student.id}. Reason: {error_msg}"
                    ) from exc
                else:
                    LOGGER.warning(
                        f"Unable to award program certificate to user {student.id} in program {program_uuid}. The "
                        "program might not be configured correctly in Credentials"
                    )
            except Exception as exc:  # pylint: disable=broad-except
                # keep trying to award other certs, but let celery retry the whole task to fix any missing entries
                LOGGER.exception(
                    f"Failed to award program certificate to user {student.id} in program {program_uuid}: {exc}"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                )
                failed_program_certificate_award_attempts.append(program_uuid)

        if failed_program_certificate_award_attempts:
            # N.B. This logic assumes that this task is idempotent
<<<<<<< HEAD
            LOGGER.info(f"Retrying failed tasks to award program certificate(s) to user {student}")
=======
            LOGGER.info(f"Retrying failed tasks to award program certificate(s) to user {student.id}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            # The error message may change on each reattempt but will never be raised until the max number of retries
            # have been exceeded. It is unlikely that this list will change by the time it reaches its maximimum number
            # of attempts.
            error_msg = (
<<<<<<< HEAD
                f"Failed to award program certificate(s) for user {student} in programs "
                f"{failed_program_certificate_award_attempts}"
            )
            raise _retry_with_custom_exception(username=username, reason=error_msg, countdown=countdown)
    else:
        LOGGER.warning(f"User {student} is not eligible for any new program certificates")

    LOGGER.info(f"Successfully completed the task award_program_certificates for user {student}")


# pylint: disable=W0613
@shared_task(bind=True, ignore_result=True)
=======
                f"Failed to award program certificate(s) for user {student.id} in programs "
                f"{failed_program_certificate_award_attempts}"
            )
            raise MaxRetriesExceededError(
                f"Failed to award a program certificate to user {student.id}. Reason: {error_msg}"
            )
    else:
        LOGGER.warning(f"User {student.id} is not eligible for any new program certificates")

    LOGGER.info(f"Successfully completed the task award_program_certificates for user {student.id}")


# pylint: disable=W0613
@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    max_retries=10,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@set_code_owner_attribute
def update_credentials_course_certificate_configuration_available_date(
    self, course_key, certificate_available_date=None
):
    """
    This task will update the CourseCertificate configuration's available date
<<<<<<< HEAD
    in Credentials. This is different from the "visible_date" attribute. This
    date will always either be the available date that is set in Studio for a
    given course, or it will be None.
=======
    in Credentials.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

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
    modes = [
<<<<<<< HEAD
        mode.slug for mode in course_modes
=======
        mode.slug
        for mode in course_modes
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        if mode.slug in CourseMode.CERTIFICATE_RELEVANT_MODES or CourseMode.is_eligible_for_certificate(mode.slug)
    ]
    if len(modes) != 1:
        LOGGER.exception(f"Either course {course_key} has no certificate mode or multiple modes. Task failed.")
        return

    credentials_client = get_credentials_api_client(
        User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
    )
    cert_config = {
        "course_id": course_key,
        "mode": modes[0],
    }
    post_course_certificate_configuration(
        client=credentials_client,
        cert_config=cert_config,
        certificate_available_date=certificate_available_date,
    )


<<<<<<< HEAD
@shared_task(bind=True, ignore_result=True)
=======
@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    max_retries=10,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@set_code_owner_attribute
def award_course_certificate(self, username, course_run_key):
    """
    This task is designed to be called whenever a student GeneratedCertificate is updated, or when a course-run's
    `certificate_available_date` value is updated.

    It can be called independently for a username and a course_run, but is invoked on each GeneratedCertificate.save.

<<<<<<< HEAD
    If this function is moved, make sure to update it's entry in EXPLICIT_QUEUES in the settings files so it runs in the
=======
    If this function is moved, make sure to update its entry in EXPLICIT_QUEUES in the settings files so it runs in the
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    correct queue.

    Arguments:
        username (str): The user to award the Credentials course cert to
        course_run_key (str): The course run key to award the certificate for
    """
<<<<<<< HEAD
    def _retry_with_custom_exception(username, course_run_key, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to award course certificate for user {username} for course {course_run_key}. Reason: {reason}"
        )
        return self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)

    countdown = 2**self.request.retries

    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  Since this is a recoverable situation,
    # mark this task for retry instead of failing it altogether.
=======
    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  This is a recoverable situation, let celery retry.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    if not is_credentials_enabled():
        error_msg = (
            "Task award_course_certificate cannot be executed when credentials issuance is disabled in API config"
        )
        LOGGER.warning(error_msg)
<<<<<<< HEAD
        raise _retry_with_custom_exception(
            username=username,
            course_run_key=course_run_key,
            reason=error_msg,
            countdown=countdown,
        )
=======
        raise MaxRetriesExceededError(f"Failed to award course certificate. Reason: {error_msg}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        LOGGER.warning(
            "Task award_course_certificate was called with an invalid username. Could not retrieve a User instance "
            f"with username {username}"
        )
        return

<<<<<<< HEAD
    LOGGER.info(f"Running task award_course_certificate for user {user}")
    try:
        course_key = CourseKey.from_string(course_run_key)
        # Get the cert for the course key and username if it's both passing and available in professional/verified
        try:
            certificate = GeneratedCertificate.eligible_certificates.get(
                user=user.id,
                course_id=course_key,
            )
        except GeneratedCertificate.DoesNotExist:
            LOGGER.warning(
                f"Task award_course_certificate was called for user {user} in course run {course_key} but this learner "
                "has not earned a course certificate in this course run"
            )
            return

        if (
            certificate.mode in CourseMode.CERTIFICATE_RELEVANT_MODES
            or CourseMode.is_eligible_for_certificate(certificate.mode)
        ):
            course_overview = get_course_overview_or_none(course_key)
            if not course_overview:
                LOGGER.warning(
                    f"Task award_course_certificate was called for user {user} in course {course_key} but no course "
                    "overview could be retrieved for the course run"
                )
                return

            visible_date = available_date_for_certificate(course_overview, certificate)
            LOGGER.info(
                f"Task award_course_certificate will award a course certificate to user {user} in course run "
                f"{course_key} with a visible date of {visible_date}"
            )

            # If the certificate has an associated CertificateDateOverride, send it along
            try:
                date_override = certificate.date_override.date
                LOGGER.info(
                    f"Task award_course_certificate will award a course certificate to user {user} in course run "
                    f"{course_key} with an override date of {date_override}"
                )
            except ObjectDoesNotExist:
                date_override = None

            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )
            post_course_certificate(
                credentials_client,
                username,
                certificate,
                visible_date,
                date_override,
                org=course_key.org,
            )
            LOGGER.info(f"Awarded a course certificate to user {user} in course run {course_key}")
    except Exception as exc:
        error_msg = f"Failed to determine course certificates to be awarded for user {user}."
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_run_key=course_run_key,
            reason=error_msg,
            countdown=countdown,
        ) from exc


@shared_task(bind=True, ignore_result=True)
=======
    LOGGER.info(f"Running task award_course_certificate for user {user.id}")
    try:
        course_key = CourseKey.from_string(course_run_key)
    except InvalidKeyError as exc:
        error_msg = "Failed to determine course key"
        LOGGER.warning(
            f"Failed to award course certificate for user {user.id} for course {course_run_key}. Reason: {error_msg}"
        )
        return

    # Get the cert for the course key and username if it's both passing and available in professional/verified
    try:
        certificate = GeneratedCertificate.eligible_certificates.get(
            user=user.id,
            course_id=course_key,
        )
    except GeneratedCertificate.DoesNotExist:
        LOGGER.warning(
            f"Task award_course_certificate was called for user {user.id} in course run {course_key} but this learner "
            "has not earned a course certificate in this course run"
        )
        return

    try:
        if (
            certificate.mode not in CourseMode.CERTIFICATE_RELEVANT_MODES
            and not CourseMode.is_eligible_for_certificate(certificate.mode)
        ):
            LOGGER.warning(
                f"Task award_course_certificate was called for user {user.id} in course run {course_key} but "
                f"this course has an ineligible mode of {certificate.mode} for a certificate on this instance."
            )
            return
    except Exception as exc:
        error_msg = f"Failed to determine course mode certificate eligibility for {certificate}."
        LOGGER.error(error_msg)
        raise MaxRetriesExceededError(
            f"Failed to award course certificate for user {user.id} for course {course_run_key}. Reason: {error_msg}"
        ) from exc

    course_overview = get_course_overview_or_none(course_key)
    if not course_overview:
        LOGGER.warning(
            f"Task award_course_certificate was called for user {user.id} in course {course_key} but no course "
            "overview could be retrieved for the course run"
        )
        return

    # If the certificate has an associated CertificateDateOverride, send it along
    try:
        date_override = certificate.date_override.date  # type: Optional["datetime"]
        LOGGER.info(
            f"Task award_course_certificate will award a course certificate to user {user.id} in course run "
            f"{course_key} with an override date of {date_override}"
        )
    except ObjectDoesNotExist:
        date_override = None  # type: Optional["datetime"]

    try:
        credentials_client = get_credentials_api_client(
            User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
        )
        post_course_certificate(
            credentials_client,
            username,
            certificate,
            date_override,
            org=course_key.org,
        )
    except Exception as exc:
        error_msg = f"Failed to post course certificate to be awarded for user {user.id}."
        raise MaxRetriesExceededError(
            f"Failed to award course certificate for user {user.id} for course {course_run_key}. Reason: {error_msg}"
        ) from exc

    # Successfully posted the cert to credentials
    LOGGER.info(f"Awarded a course certificate to user {user.id} in course run {course_key}")


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    max_retries=10,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@set_code_owner_attribute
def revoke_program_certificates(self, username, course_key):  # lint-amnesty, pylint: disable=too-many-statements
    """
    This task is designed to be called whenever a student's course certificate is revoked.

    It will consult with a variety of APIs to determine whether or not the specified user's certificate should be
    revoked in one or more programs, and use the credentials service to revoke the said certificates if so.

<<<<<<< HEAD
    If this function is moved, make sure to update it's entry in EXPLICIT_QUEUES in the settings files so it runs in the
=======
    If this function is moved, make sure to update its entry in EXPLICIT_QUEUES in the settings files so it runs in the
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    correct queue.

    Args:
        username (str): The username of the student
        course_key (str): The course identifier

    Returns:
        None
    """
<<<<<<< HEAD
    def _retry_with_custom_exception(username, course_key, reason, countdown):
        exception = MaxRetriesExceededError(
            f"Failed to revoke program certificate for user {username} for course {course_key}. Reason: {reason}"
        )
        return self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)

    countdown = 2**self.request.retries

    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  Since this is a recoverable situation, mark this task for retry instead of
    # failing it altogether.
=======
    # If the credentials config model is disabled for this feature, it may indicate a condition where processing of such
    # tasks has been temporarily disabled.  Since this is a recoverable situation, let celery retry.
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    if not is_credentials_enabled():
        error_msg = (
            "Task revoke_program_certificates cannot be executed, use of the Credentials service is disabled by config"
        )
        LOGGER.warning(error_msg)
<<<<<<< HEAD
        raise _retry_with_custom_exception(
            username=username,
            course_key=course_key,
            reason=error_msg,
            countdown=countdown,
        )
=======
        raise MaxRetriesExceededError(f"Failed to revoke program certificate. Reason: {error_msg}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    try:
        student = User.objects.get(username=username)
    except User.DoesNotExist:
        LOGGER.warning(
            "Task revoke_program_certificates was called with an invalid username. Could not retrieve a User instance "
            f"with username {username}"
        )
        return

<<<<<<< HEAD
    LOGGER.info(f"Running task revoke_program_certificates for user {student}")
=======
    LOGGER.info(f"Running task revoke_program_certificates for user {student.id}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    try:
        inverted_programs = get_inverted_programs(student)
        course_specific_programs = inverted_programs.get(course_key)
        if not course_specific_programs:
            LOGGER.warning(
<<<<<<< HEAD
                f"Task revoke_program_certificates was called for user {student} and course run {course_key} with no "
                "engaged programs"
=======
                f"Task revoke_program_certificates was called for user {student.id} and course run {course_key} with "
                "no engaged programs"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            )
            return

        # Determine which program certificates the user has already been awarded, if any.
        program_uuids_to_revoke = get_revokable_program_uuids(course_specific_programs, student)
    except Exception as exc:
        error_msg = (
            f"Failed to determine if any program certificates associated with course run {course_key} should be "
<<<<<<< HEAD
            f"revoked from user {student}"
        )
        LOGGER.exception(error_msg)
        raise _retry_with_custom_exception(
            username=username,
            course_key=course_key,
            reason=error_msg,
            countdown=countdown,
=======
            f"revoked from user {student.id}"
        )
        LOGGER.exception(error_msg)
        raise MaxRetriesExceededError(
            f"Failed to revoke program certificate for user {student.id} for course {course_key}. Reason: {error_msg}"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
        ) from exc

    if program_uuids_to_revoke:
        try:
            credentials_client = get_credentials_api_client(
                User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
            )
        except Exception as exc:
            error_msg = "Failed to create a credentials API client to revoke program certificates"
            LOGGER.exception(error_msg)
<<<<<<< HEAD
            # Retry because a misconfiguration could be fixed
            raise _retry_with_custom_exception(username, course_key, reason=exc, countdown=countdown) from exc
=======
            # Stil retryable because a misconfiguration could be fixed
            raise MaxRetriesExceededError(
                f"Failed to revoke program certificate for user {student.id} for course {course_key}. Reason: {exc}"
            ) from exc
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

        failed_program_certificate_revoke_attempts = []
        for program_uuid in program_uuids_to_revoke:
            try:
                revoke_program_certificate(credentials_client, username, program_uuid)
<<<<<<< HEAD
                LOGGER.info(f"Revoked program certificate from user {student} in program {program_uuid}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.warning(
                        f"Unable to revoke program certificate from user {student} in program {program_uuid}, a "
                        "program certificate could not be found"
                    )
                elif exc.response.status_code == 429:
                    rate_limit_countdown = 60
                    error_msg = (
                        f"Rate limited. Retrying task to revoke a program certificate from user {student} in program "
                        f"{program_uuid} in {rate_limit_countdown} seconds"
                    )
                    LOGGER.warning(error_msg)
                    # Retry after 60 seconds, when we should be in a new throttling window
                    raise _retry_with_custom_exception(
                        username,
                        course_key,
                        reason=error_msg,
                        countdown=rate_limit_countdown,
                    ) from exc
                else:
                    LOGGER.warning(
                        f"Unable to revoke program certificate from user {student} in program {program_uuid}"
                    )
            except Exception as exc:  # pylint: disable=broad-except
                # keep trying to revoke other certs, but retry the whole task to fix any missing entries
                LOGGER.exception(
                    f"Failed to revoke program certificate from user {student} in program {program_uuid}: {exc}"
=======
                LOGGER.info(f"Revoked program certificate from user {student.id} in program {program_uuid}")
            except HTTPError as exc:
                if exc.response.status_code == 404:
                    LOGGER.warning(
                        f"Unable to revoke program certificate from user {student.id} in program {program_uuid}, a "
                        "program certificate could not be found"
                    )
                elif exc.response.status_code == 429:
                    # Let celery handle retry attempts and backoff
                    error_msg = (
                        f"Rate limited. Attempting to revoke a program certificate from user {student.id} in program "
                        f"{program_uuid}."
                    )
                    LOGGER.warning(error_msg)
                    raise MaxRetriesExceededError(
                        f"Failed to revoke program certificate for user {student.id} Reason: {error_msg}"
                    ) from exc
                else:
                    LOGGER.warning(
                        f"Unable to revoke program certificate from user {student.id} in program {program_uuid}"
                    )
            except Exception as exc:  # pylint: disable=broad-except
                # keep trying to revoke other certs, but let celery retry the whole task to fix any missing entries
                LOGGER.exception(
                    f"Failed to revoke program certificate from user {student.id} in program {program_uuid}: {exc}"
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
                )
                failed_program_certificate_revoke_attempts.append(program_uuid)

        if failed_program_certificate_revoke_attempts:
            # N.B. This logic assumes that this task is idempotent
<<<<<<< HEAD
            LOGGER.info(f"Retrying failed task to revoke program certificate(s) from user {student}")
=======
            LOGGER.info(f"Failed task to revoke program certificate(s) from user {student .id}")
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
            # The error message may change on each reattempt but will never be raised until the max number of retries
            # have been exceeded. It is unlikely that this list will change by the time it reaches its maximimum number
            # of attempts.
            error_msg = (
<<<<<<< HEAD
                f"Failed to revoke program certificate(s) from user {student} for programs "
                f"{failed_program_certificate_revoke_attempts}"
            )
            raise _retry_with_custom_exception(username, course_key, reason=error_msg, countdown=countdown)
    else:
        LOGGER.info(f"No program certificates to revoke from user {student}")

    LOGGER.info(f"Successfully completed the task revoke_program_certificates for user {student}")


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
    countdown = 2**self.request.retries

    # If the CredentialsApiConfig configuration model is disabled for this feature, it may indicate a condition where
    # processing of such tasks has been temporarily disabled. Since this is a recoverable situation, mark this task for
    # retry instead of failing it.
    if not is_credentials_enabled():
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
    users_with_certificates_in_course = GeneratedCertificate.eligible_available_certificates.filter(
        course_id=course_key
    ).values_list("user__username", flat=True)

    LOGGER.info(
        f"Resending course certificates for learners in course {course_key} to the Credentials service. Queueing "
        f"{len(users_with_certificates_in_course)} `award_course_certificate` tasks."
    )
    for user in users_with_certificates_in_course:
        award_course_certificate.delay(user, str(course_key))


@shared_task(bind=True, ignore_result=True)
=======
                f"Failed to revoke program certificate(s) from user {student.id} for programs "
                f"{failed_program_certificate_revoke_attempts}"
            )
            raise MaxRetriesExceededError(
                f"Failed to revoke program certificate for user {student.id} for course {course_key}. "
                f"Reason: {error_msg}"
            )
    else:
        LOGGER.info(f"No program certificates to revoke from user {student.id}")

    LOGGER.info(f"Successfully completed the task revoke_program_certificates for user {student.id}")


@shared_task(
    bind=True,
    ignore_result=True,
    autoretry_for=(Exception,),
    max_retries=10,
    retry_backoff=30,
    retry_backoff_max=600,
    retry_jitter=True,
)
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
@set_code_owner_attribute
def update_certificate_available_date_on_course_update(self, course_key):
    """
    This task is designed to be enqueued whenever a course run's Certificate Display Behavior (CDB) or Certificate
    Available Date (CAD) has been updated in the CMS.

    When executed, this task is responsible for enqueuing an additional subtask responsible for syncing the updated CAD
    value in the Credentials IDA's internal records.

    Args:
        course_key(str): The course run's identifier
    """
<<<<<<< HEAD
    countdown = 2**self.request.retries

=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    # If the CredentialsApiConfig configuration model is disabled for this feature, it may indicate a condition where
    # processing of such tasks has been temporarily disabled. Since this is a recoverable situation, mark this task for
    # retry instead of failing it.
    if not is_credentials_enabled():
        error_msg = (
<<<<<<< HEAD
            "Cannot execute the `update_certificate_visible_date_on_course_update` task. Issuing user credentials "
            "through the Credentials IDA is disabled."
        )
        LOGGER.warning(error_msg)
        exception = MaxRetriesExceededError(
            "Failed to update the `certificate_available_date` in the Credentials service for course-run "
            f"{course_key}. Reason: {error_msg}"
        )
        raise self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)
=======
            "Cannot execute the `update_certificate_available_date_on_course_update` task. Issuing user credentials "
            "through the Credentials IDA is disabled."
        )
        LOGGER.warning(error_msg)
        raise MaxRetriesExceededError(
            "Failed to update the `certificate_available_date` in the Credentials service for course-run "
            f"{course_key}. Reason: {error_msg}"
        )
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

    course_overview = get_course_overview_or_none(course_key)
    if not course_overview:
        LOGGER.warning(
            f"Unable to send the updated certificate available date of course run [{course_key}] to Credentials. A "
            "course overview for this course run could not be found"
        )
        return

    # When updating the certificate available date of instructor-paced course runs,
    #   - If the display behavior is set to "A date after the course end date" (END_WITH_DATE), we should send the
    #     certificate available date set by the course team in Studio (and stored as part of the course runs Course
    #     Overview)
    #   - If the display behavior is set to "End date of course" (END), we should send the end date of the course run
    #     as the certificate available date. We send the end date because the Credentials IDA doesn't understand the
    #     concept of course pacing and needs an explicit date in order to correctly gate the visibility of course and
    #     program certificates.
    #   - If the display behavior is set to "Immediately upon passing" (EARLY_NO_INFO), we should always send None for
    #     the course runs certificate available date. A course run configured with this display behavior must not have a
    #     certificate available date associated with or the Credentials system will incorrectly hide certificates from
    #     learners.
    if course_overview.self_paced is False:
        if course_overview.certificates_display_behavior == CertificatesDisplayBehaviors.END_WITH_DATE:
            new_certificate_available_date = str(course_overview.certificate_available_date)
        elif course_overview.certificates_display_behavior == CertificatesDisplayBehaviors.END:
            new_certificate_available_date = str(course_overview.end)  # `end_date` is deprecated, use `end` instead
        elif course_overview.certificates_display_behavior == CertificatesDisplayBehaviors.EARLY_NO_INFO:
            new_certificate_available_date = None
    # Else, this course run is self-paced, and having a certificate available date associated with a self-paced course
    # run is not allowed. Course runs with this type of pacing should always award a certificate to learners immediately
    # upon passing. If the system detects that an update must be sent to Credentials, we *always* send a certificate
    # available date of `None`. We are aware of a defect that sometimes allows a certificate available date to be saved
    # for a self-paced course run. This is an attempt to prevent bad data from being synced to the Credentials service
    # too.
    else:
        new_certificate_available_date = None

    update_credentials_course_certificate_configuration_available_date.delay(
<<<<<<< HEAD
        str(course_key),
        new_certificate_available_date
=======
        str(course_key), new_certificate_available_date
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    )
