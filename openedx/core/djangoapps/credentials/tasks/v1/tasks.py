"""
This file contains Celery tasks and utility functions supporting the Credentials IDA.
"""
import math
import time
from urllib.parse import urljoin

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from celery_utils.logged_task import LoggedTask
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from edx_django_utils.monitoring import set_code_owner_attribute
from MySQLdb import OperationalError
from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.api import get_recently_modified_certificates
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.grades.api import CourseGradeFactory, get_recently_modified_grades
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.credentials.helpers import is_learner_records_enabled_for_org
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig
from openedx.core.djangoapps.credentials.utils import get_credentials_api_base_url, get_credentials_api_client
from openedx.core.djangoapps.programs.signals import (
    handle_course_cert_awarded,
    handle_course_cert_changed,
    handle_course_cert_revoked,
)
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration

User = get_user_model()
logger = get_task_logger(__name__)

# "Interesting" means "The Credentials IDA will want to know about it"
INTERESTING_MODES = CourseMode.CERTIFICATE_RELEVANT_MODES
INTERESTING_STATUSES = [
    CertificateStatuses.notpassing,
    CertificateStatuses.downloadable,
]

# Maximum number of retries before giving up. For reference, 11 retries with exponential backoff yields a maximum
# waiting time of 2047 seconds (about 30 minutes). Setting this to None could yield unwanted behavior: infinite retries.
MAX_RETRIES = 11


@shared_task(bind=True, ignore_result=True)
@set_code_owner_attribute
def send_grade_to_credentials(
    self,
    username,
    course_run_key,
    verified,
    letter_grade,
    percent_grade,
    grade_last_updated
):
    """
    Celery task to notify the Credentials IDA of an "interesting" grade change via an API call.

    Args:
        username (string): The username of the learner we are currently processing
        course_run_key (string): String identifier of the course run associated with the grade update
        verified (bool): Boolean determining if the course run is in a "verified" track
        letter_grade (string): String identifier describing the "letter" grade the learner has earned
        percent_grade (float): Number representing the learner's grade in this course run
        grade_last_updated (string): String describing the last time this grade was modified in the LMS
    """
    logger.info(f"Running task send_grade_to_credentials for username {username} and course {course_run_key}")

    countdown = 2 ** self.request.retries
    course_key = CourseKey.from_string(course_run_key)

    try:
        credentials_client = get_credentials_api_client(
            User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME)
        )
        api_url = urljoin(f"{get_credentials_api_base_url(org=course_key.org)}/", "grades/")
        response = credentials_client.post(
            api_url,
            data={
                'username': username,
                'course_run': course_run_key,
                'letter_grade': letter_grade,
                'percent_grade': percent_grade,
                'verified': verified,
                'lms_last_updated_at': grade_last_updated
            }
        )
        response.raise_for_status()
        logger.info(f"Sent grade for course {course_run_key} for user {username}")
    except Exception:  # lint-amnesty, pylint: disable=W0703
        grade_str = f'(percent: {percent_grade} letter: {letter_grade})'
        error_msg = f'Failed to send grade {grade_str} for course {course_run_key} for user {username}.'
        logger.exception(error_msg)
        exception = MaxRetriesExceededError(f"Failed to send grade to credentials. Reason: {error_msg}")
        raise self.retry(exc=exception, countdown=countdown, max_retries=MAX_RETRIES)  # pylint: disable=raise-missing-from


@shared_task(base=LoggedTask, ignore_result=True)
@set_code_owner_attribute
def handle_notify_credentials(options, course_keys):
    """
    Celery task to handle the notify_credentials management command. Finds the relevant cert and grade records, then
    starts other celery tasks to send the data.

    Args:
        options (dict): Dictionary containing settings for this run of the `handle_notify_credentials` task
        course_keys (list[string]): List of course run keys for this run of the `handle_notify_credentials` task
    """
    try:
        site_config = SiteConfiguration.objects.get(site__domain=options['site']) if options['site'] else None
    except SiteConfiguration.DoesNotExist:
        logger.exception('No site configuration found for site %s', options['site'])
        return

    # If a `start_date` or `end_date` are included in the options we should also include certificates with a
    # CertificateDateOveride modified within the time range
    certs = get_recently_modified_certificates(
        course_keys,
        options['start_date'],
        options['end_date'],
        options['user_ids']
    )

    users = None
    if options['user_ids']:
        users = User.objects.filter(id__in=options['user_ids'])

    grades = get_recently_modified_grades(
        course_keys,
        options['start_date'],
        options['end_date'],
        users
    )

    logger.info(
        f"[notify_credentials] Sending notifications for {certs.count()} certificates and {grades.count()} grades"
    )
    if options['dry_run']:
        log_dry_run(certs, grades)
    else:
        send_notifications(
            certs,
            grades,
            site_config=site_config,
            delay=options['delay'],
            page_size=options['page_size'],
            verbose=options['verbose'],
            notify_programs=options['notify_programs'],
            revoke_program_certs=options['revoke_program_certs']
        )


def send_notifications(
    certs,
    grades,
    site_config=None,
    delay=0,
    page_size=100,
    verbose=False,
    notify_programs=False,
    revoke_program_certs=False
):
    """
    Utility function responsible for bootstrapping certificate and grade updates to the Credentials IDA. We do this by
    invoking existing code paths that should force the LMS to (re-)send data to Credentials.

    First, we directly call our Django signal handlers responsible for updating the status of certificates throughout
    the system. This will trigger attempts to send certificate status information to the Credentials IDA.

    Then, we call a utility function (`send_grade_if_interesting`) that is responsible for determining if the
    Credentials IDA cares about this particular grade update for a learner.

    Args:
        certs (QuerySet): A collection of course certificates associated with the users we need to update
        grades (QuerySet): A collection of grades associated with the users we need to update
        site_config (SiteConfiguration): Optional, may be None. The site associated with the users we need to update.
        delay (int): Delay (in seconds) to wait between queries
        page_size (int): Number of records to process from the certs or grades QuerySet at once. Used to handle load.
        verbose (bool): Used to determine level of logging output during grade updates
        notify_programs (bool): Used to determine if an update should be sent to Credentials
        revoke_program_certs (bool): Used to determine if the system should attempt revoking program certificates during
         this run of the `notify_credentials` management command
    """
    course_cert_info = {}
    # First, do certs
    for i, cert in paged_query(certs, delay, page_size):
        if site_config and not site_config.has_org(cert.course_id.org):
            logger.info("Skipping credential changes %d for certificate %s", i, certstr(cert))
            continue

        logger.info(f"Handling credential change {i} for certificate {certstr(cert)}")
        signal_args = {
            'sender': None,
            'user': cert.user,
            'course_key': cert.course_id,
            'mode': cert.mode,
            'status': cert.status,
            'verbose': verbose,
        }

        data = {
            'mode': cert.mode,
            'status': cert.status
        }
        course_cert_info[(cert.user.id, str(cert.course_id))] = data
        # handles awarding course certificates in Credentials
        handle_course_cert_changed(**signal_args)
        # handles awarding program certificates in Credentials
        if notify_programs and CertificateStatuses.is_passing_status(cert.status):
            handle_course_cert_awarded(**signal_args)
        # handles revoking program certificates in Credentials
        if revoke_program_certs and notify_programs and not CertificateStatuses.is_passing_status(cert.status):
            handle_course_cert_revoked(**signal_args)

    # Then do grades
    for i, grade in paged_query(grades, delay, page_size):
        if site_config and not site_config.has_org(grade.course_id.org):
            logger.info(f"Skipping grade change {i} for grade in {gradestr(grade)}")
            continue

        logger.info(f"Handling grade change {i} for grade in {gradestr(grade)}")
        user = User.objects.get(id=grade.user_id)

        # Grab mode/status from cert call
        key = (user.id, str(grade.course_id))
        cert_info = course_cert_info.get(key, {})
        mode = cert_info.get('mode', None)
        status = cert_info.get('status', None)

        send_grade_if_interesting(
            user,
            grade.course_id,
            mode,
            status,
            grade.letter_grade,
            grade.percent_grade,
            grade_last_updated=grade.modified,
            verbose=verbose
        )


def paged_query(queryset, delay, page_size):
    """
    A generator that iterates through a queryset but only resolves chunks of it at once, to avoid overwhelming memory
    with a giant query. Also adds an optional delay between yields, to help with load.
    """
    count = queryset.count()
    pages = int(math.ceil(count / page_size))

    for page in range(pages):
        page_start = page * page_size
        page_end = page_start + page_size
        subquery = queryset[page_start:page_end]

        if delay and page:
            time.sleep(delay)
        index = 0
        try:
            for item in subquery.iterator():
                index += 1
                yield page_start + index, item
        except OperationalError:
            # When running the notify_credentials command locally there is an
            # OperationalError thrown by MySQL when there are no more results
            # available for the queryset iterator. This change catches that exception,
            # checks state, and then logs according to that state. This code runs in
            # production without issue. This changes allows for the code to be run
            # locally without a separate code path.
            if index == count:
                logger.info('OperationalError Exception caught, all known results processed in paged_query')
            else:
                logger.warning('OperationalError Exception caught, it is possible some results were missed')
            continue


def log_dry_run(certs, grades):
    """Give a preview of what certs/grades we will handle."""
    logger.info("DRY-RUN: This task would have handled changes for...")
    ITEMS_TO_SHOW = 10

    logger.info(f"{certs.count()} Certificates:")
    for cert in certs[:ITEMS_TO_SHOW]:
        logger.info(f"\t{certstr(cert)}")
    if certs.count() > ITEMS_TO_SHOW:
        logger.info(f"\t(+ {certs.count() - ITEMS_TO_SHOW} more)")

    logger.info(f"{grades.count()} Grades:")
    for grade in grades[:ITEMS_TO_SHOW]:
        logger.info(f"\t{gradestr(grade)}")
    if grades.count() > ITEMS_TO_SHOW:
        logger.info(f"\t(+ {grades.count() - ITEMS_TO_SHOW} more)")


def certstr(cert):
    return f'{cert.course_id} for user {cert.user.id}'


def gradestr(grade):
    return f'{grade.course_id} for user {grade.user_id}'


def send_grade_if_interesting(
    user,
    course_run_key,
    mode,
    status,
    letter_grade,
    percent_grade,
    grade_last_updated=None,
    verbose=False
):
    """
    Checks if a grade is interesting to Credentials and schedules a Celery task if so. This is Credentials business
    logic that has bled into the LMS. We want to filter here in order to not flood our task queue with a bunch of
    signals, so we put up with it.

    Args:
        user (User): User associated with this grade update
        course_run_key (CourseLocator): The course run key associated with this grade update
        mode (string): The "mode" for the specific course run (e.g. "verified", "audit", etc.)
        status (string): The status of the Certificate associated with this grade update
        letter_grade (string): The letter grade associated with this grade update (e.g. "A", "B", or "pass" or "fail")
        percent_grade (float): A number representing the learner's grade in this course run
        grade_last_updated (DateTime): DateTime object representing the last time the (percent) grade was updated in the
         LMS.
        verbose (bool): A value determining the logging level desired for this grade update
    """
    if verbose:
        msg = (
            f"Starting send_grade_if_interesting with_params: user [{getattr(user, 'username', None)}], "
            f"course_run_key [{course_run_key}], mode [{mode}], status [{status}], letter_grade [{letter_grade}], "
            f"percent_grade [{percent_grade}], grade_last_updated [{grade_last_updated}], verbose [{verbose}]"
        )
        logger.info(msg)

    # Avoid scheduling new tasks if certification is disabled. (Grades are a part of the records/cert story)
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        if verbose:
            logger.info("Skipping send grade: is_learner_issuance_enabled False")
        return

    # Avoid scheduling new tasks if learner records are disabled for this site.
    if not is_learner_records_enabled_for_org(course_run_key.org):
        if verbose:
            logger.info(
                "Skipping send grade: ENABLE_LEARNER_RECORDS False for org [{org}]".format(
                    org=course_run_key.org
                )
            )
        return

    # Grab mode/status if we don't have them in hand
    if mode is None or status is None:
        try:
            cert = GeneratedCertificate.objects.get(user=user, course_id=course_run_key)  # pylint: disable=no-member
            mode = cert.mode
            status = cert.status
        except GeneratedCertificate.DoesNotExist:
            # We only care about grades for which there is a certificate.
            if verbose:
                logger.info(
                    f"Skipping send grade: no cert for user [{getattr(user, 'username', None)}] & course_id "
                    f"[{course_run_key}]"
                )
            return

    # Don't worry about whether it's available as well as awarded. Just awarded is good enough to record a verified
    # attempt at a course. We want even the grades that didn't pass the class because Credentials wants to know about
    # those too.
    if mode not in INTERESTING_MODES or status not in INTERESTING_STATUSES:
        if verbose:
            logger.info(f"Skipping send grade: mode/status uninteresting for mode [{mode}] & status [{status}]")
        return

    # If the course isn't in any program, don't bother telling Credentials about it. When Credentials grows support
    # for course records as well as program records, we'll need to open this up.
    if not is_course_run_in_a_program(course_run_key):
        if verbose:
            logger.info(
                f"Skipping send grade: course run not in a program. [{course_run_key}]"
            )
        return

    # Grab grade data if we don't have them in hand
    if letter_grade is None or percent_grade is None or grade_last_updated is None:
        grade = CourseGradeFactory().read(user, course_key=course_run_key, create_if_needed=False)
        if grade is None:
            if verbose:
                logger.info(
                    f"Skipping send grade: No grade found for user [{getattr(user, 'username', None)}] & course_id "
                    f"[{course_run_key}]"
                )
            return
        letter_grade = grade.letter_grade
        percent_grade = grade.percent
        grade_last_updated = grade.last_updated

    send_grade_to_credentials.delay(
        user.username,
        str(course_run_key),
        True,
        letter_grade,
        percent_grade,
        grade_last_updated
    )


def is_course_run_in_a_program(course_run_key):
    """
    Returns true if the given course key is in any program at all. This functionality depends on data to be present in
    the program cache. We don't have an easy way to determine if a course run is in a program, so we must search through
    each program (on a site-by-site basis).

    Args:
        course_run_key (CourseLocator): The course run key used we are using to verify program membership

    Returns:
        A boolean describing if the course run is part of a program
    """
    sites = Site.objects.all()
    str_key = str(course_run_key)
    for site in sites:
        for program in get_programs(site):
            for course in program['courses']:
                for course_run in course['course_runs']:
                    if str_key == course_run['key']:
                        return True
    return False


@shared_task(base=LoggedTask, ignore_result=True)
@set_code_owner_attribute
def backfill_date_for_all_course_runs():
    """
    This task will update the course certificate configuration's certificate_available_date in credentials for all
    course runs. This is different from the "visable_date" attribute. This date will either be the available date that
    is set in studio for a given course, or it will be None. This will exclude any course runs that do not have a
    certificate_available_date or are self paced.
    """
    course_run_list = CourseOverview.objects.exclude(self_paced=True).exclude(certificate_available_date=None)
    for index, course_run in enumerate(course_run_list):
        logger.info(
            f"updating certificate_available_date for course {course_run.id} "
            f"with date {course_run.certificate_available_date}"
        )
        course_key = str(course_run.id)
        course_modes = CourseMode.objects.filter(course_id=course_key)
        # There should only ever be one certificate relevant mode per course run
        modes = [mode.slug for mode in course_modes if mode.slug in CourseMode.CERTIFICATE_RELEVANT_MODES]
        if len(modes) != 1:
            logger.exception(
                f'Either course {course_key} has no certificate mode or multiple modes. Task failed.'
            )
        # if there is only one relevant mode, post to credentials
        else:
            try:
                credentials_client = get_credentials_api_client(
                    User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
                )
                api_url = urljoin(f"{get_credentials_api_base_url()}/", "course_certificates/")
                response = credentials_client.post(
                    api_url,
                    json={
                        "course_id": course_key,
                        "certificate_type": modes[0],
                        "certificate_available_date": course_run.certificate_available_date.strftime(
                            '%Y-%m-%dT%H:%M:%SZ'
                        ),
                        "is_active": True,
                    }
                )
                response.raise_for_status()

                logger.info(f"certificate_available_date updated for course {course_key}")
            except Exception:  # lint-amnesty, pylint: disable=W0703
                error_msg = f"Failed to send certificate_available_date for course {course_key}."
                logger.exception(error_msg)
        if index % 10 == 0:
            time.sleep(3)


@shared_task(base=LoggedTask, ignore_result=True)
@set_code_owner_attribute
def clean_certificate_available_date():
    """
    Historically, when courses changed their certificates_display_behavior, the certificate_available_date was not
    updating properly. This task will clean out course runs that have a misconfigured certificate available date in the
    Credentials IDA.
    """
    course_run_list = CourseOverview.objects.exclude(
        self_paced=0,
        certificates_display_behavior="end",
        certificate_available_date__isnull=False
    )
    for index, course_run in enumerate(course_run_list):
        logger.info(f"removing certificate_available_date for course {course_run.id}")
        course_key = str(course_run.id)
        course_modes = CourseMode.objects.filter(course_id=course_key)
        # There should only ever be one certificate relevant mode per course run
        modes = [mode.slug for mode in course_modes if mode.slug in CourseMode.CERTIFICATE_RELEVANT_MODES]
        if len(modes) != 1:
            logger.exception(f'Either course {course_key} has no certificate mode or multiple modes. Task failed.')
        # if there is only one relevant mode, post to credentials
        else:
            try:
                credentials_client = get_credentials_api_client(
                    User.objects.get(username=settings.CREDENTIALS_SERVICE_USERNAME),
                )
                credentials_api_base_url = get_credentials_api_base_url()
                api_url = urljoin(f"{credentials_api_base_url}/", "course_certificates/")
                response = credentials_client.post(
                    api_url,
                    json={
                        "course_id": course_key,
                        "certificate_type": modes[0],
                        "certificate_available_date": None,
                        "is_active": True,
                    }
                )
                response.raise_for_status()
                logger.info(f"certificate_available_date updated for course {course_key}")
            except Exception:  # lint-amnesty, pylint: disable=W0703
                error_msg = f"Failed to send certificate_available_date for course {course_key}."
                logger.exception(error_msg)
        if index % 10 == 0:
            time.sleep(3)
