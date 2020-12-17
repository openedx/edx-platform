"""
This file contains signal handlers for credentials-related functionality.
"""


from logging import getLogger

from django.contrib.sites.models import Site

from common.djangoapps.course_modes.models import CourseMode
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.grades.api import CourseGradeFactory
from openedx.core.djangoapps.catalog.utils import get_programs
from openedx.core.djangoapps.credentials.models import CredentialsApiConfig

from .helpers import is_learner_records_enabled, is_learner_records_enabled_for_org
from .tasks.v1.tasks import send_grade_to_credentials

log = getLogger(__name__)


# "interesting" here means "credentials will want to know about it"
INTERESTING_MODES = CourseMode.CERTIFICATE_RELEVANT_MODES
INTERESTING_STATUSES = [
    CertificateStatuses.notpassing,
    CertificateStatuses.downloadable,
]


# These handlers have Credentials business logic that has bled into the LMS. But we want to filter here in order to
# not flood our task queue with a bunch of signals. So we put up with it.

def is_course_run_in_a_program(course_run_key):
    """ Returns true if the given course key is in any program at all. """

    # We don't have an easy way to go from course_run_key to a specific site that owns it. So just search each site.
    sites = Site.objects.all()
    str_key = str(course_run_key)
    for site in sites:
        for program in get_programs(site):
            for course in program['courses']:
                for course_run in course['course_runs']:
                    if str_key == course_run['key']:
                        return True
    return False


def send_grade_if_interesting(user, course_run_key, mode, status, letter_grade, percent_grade, verbose=False):
    """ Checks if grade is interesting to Credentials and schedules a Celery task if so. """

    if verbose:
        msg = u"Starting send_grade_if_interesting with params: "\
            u"user [{username}], "\
            u"course_run_key [{key}], "\
            u"mode [{mode}], "\
            u"status [{status}], "\
            u"letter_grade [{letter_grade}], "\
            u"percent_grade [{percent_grade}], "\
            u"verbose [{verbose}]"\
            .format(
                username=getattr(user, 'username', None),
                key=str(course_run_key),
                mode=mode,
                status=status,
                letter_grade=letter_grade,
                percent_grade=percent_grade,
                verbose=verbose
            )
        log.info(msg)
    # Avoid scheduling new tasks if certification is disabled. (Grades are a part of the records/cert story)
    if not CredentialsApiConfig.current().is_learner_issuance_enabled:
        if verbose:
            log.info("Skipping send grade: is_learner_issuance_enabled False")
        return

    # Avoid scheduling new tasks if learner records are disabled for this site.
    if not is_learner_records_enabled_for_org(course_run_key.org):
        if verbose:
            log.info(
                u"Skipping send grade: ENABLE_LEARNER_RECORDS False for org [{org}]".format(
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
                log.info(
                    u"Skipping send grade: no cert for user [{username}] & course_id [{course_id}]".format(
                        username=getattr(user, 'username', None),
                        course_id=str(course_run_key)
                    )
                )
            return

    # Don't worry about whether it's available as well as awarded. Just awarded is good enough to record a verified
    # attempt at a course. We want even the grades that didn't pass the class because Credentials wants to know about
    # those too.
    if mode not in INTERESTING_MODES or status not in INTERESTING_STATUSES:
        if verbose:
            log.info(
                u"Skipping send grade: mode/status uninteresting for mode [{mode}] & status [{status}]".format(
                    mode=mode,
                    status=status
                )
            )
        return

    # If the course isn't in any program, don't bother telling Credentials about it. When Credentials grows support
    # for course records as well as program records, we'll need to open this up.
    if not is_course_run_in_a_program(course_run_key):
        if verbose:
            log.info(
                u"Skipping send grade: course run not in a program. [{course_id}]".format(course_id=str(course_run_key))
            )
        return

    # Grab grades if we don't have them in hand
    if letter_grade is None or percent_grade is None:
        grade = CourseGradeFactory().read(user, course_key=course_run_key, create_if_needed=False)
        if grade is None:
            if verbose:
                log.info(
                    u"Skipping send grade: No grade found for user [{username}] & course_id [{course_id}]".format(
                        username=getattr(user, 'username', None),
                        course_id=str(course_run_key)
                    )
                )
            return
        letter_grade = grade.letter_grade
        percent_grade = grade.percent

    send_grade_to_credentials.delay(user.username, str(course_run_key), True, letter_grade, percent_grade)


def handle_grade_change(user, course_grade, course_key, **kwargs):
    """
    Notifies the Credentials IDA about certain grades it needs for its records, when a grade changes.
    """
    send_grade_if_interesting(
        user,
        course_key,
        None,
        None,
        course_grade.letter_grade,
        course_grade.percent,
        verbose=kwargs.get('verbose', False)
    )


def handle_cert_change(user, course_key, mode, status, **kwargs):
    """
    Notifies the Credentials IDA about certain grades it needs for its records, when a cert changes.
    """
    send_grade_if_interesting(user, course_key, mode, status, None, None, verbose=kwargs.get('verbose', False))
