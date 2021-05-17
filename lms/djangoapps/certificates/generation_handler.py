"""
Course certificate generation handler.

These methods check to see if a certificate can be generated (created if it does not already exist, or updated if it
exists but its state can be altered). If so, a celery task is launched to do the generation. If the certificate
cannot be generated, a message is logged and no further action is taken.
"""

import logging

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from common.djangoapps.course_modes import api as modes_api
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.models import (
    CertificateInvalidation,
    CertificateStatuses,
    CertificateWhitelist,
    GeneratedCertificate
)
from lms.djangoapps.certificates.queue import XQueueCertInterface
from lms.djangoapps.certificates.tasks import CERTIFICATE_DELAY_SECONDS, generate_certificate
from lms.djangoapps.certificates.utils import (
    emit_certificate_event,
    has_html_certificates_enabled
)
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.instructor.access import list_with_level
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

log = logging.getLogger(__name__)

WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='certificates_revamp')

# .. toggle_name: certificates_revamp.use_updated
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag to enable the updated regular (non-allowlist) course certificate logic on a
#   per-course run basis.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-03-05
# .. toggle_target_removal_date: 2022-03-05
# .. toggle_tickets: MICROBA-923
CERTIFICATES_USE_UPDATED = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='use_updated',
    module_name=__name__,
)


def can_generate_certificate_task(user, course_key):
    """
    Determine if we can create a task to generate a certificate for this user in this course run.

    This will return True if either:
    - the user is on the allowlist for the course run, or
    - the course run is using v2 course certificates
    """
    if is_on_certificate_allowlist(user, course_key):
        return True
    elif is_using_v2_course_certificates(course_key):
        return True

    return False


def generate_certificate_task(user, course_key, generation_mode=None):
    """
    Create a task to generate a certificate for this user in this course run, if the user is eligible and a certificate
    can be generated.

    If the allowlist is enabled for this course run and the user is on the allowlist, the allowlist logic will be used.
    Otherwise, the regular course certificate generation logic will be used.
    """
    if is_on_certificate_allowlist(user, course_key):
        log.info(f'User {user.id} is on the allowlist for {course_key}. Attempt will be made to generate an allowlist '
                 f'certificate.')
        return generate_allowlist_certificate_task(user, course_key, generation_mode)

    elif is_using_v2_course_certificates(course_key):
        log.info(f'{course_key} is using v2 course certificates. Attempt will be made to generate a certificate for '
                 f'user {user.id}.')
        return generate_regular_certificate_task(user, course_key, generation_mode)

    log.info(f'Neither an allowlist nor a v2 course certificate can be generated for {user.id} : {course_key}.')
    return False


def generate_allowlist_certificate_task(user, course_key, generation_mode=None):
    """
    Create a task to generate an allowlist certificate for this user in this course run.
    """
    if _can_generate_allowlist_certificate(user, course_key):
        return _generate_certificate_task(user, course_key, generation_mode)

    status = _set_allowlist_cert_status(user, course_key)
    if status is not None:
        return True

    return False


def generate_regular_certificate_task(user, course_key, generation_mode=None):
    """
    Create a task to generate a regular (non-allowlist) certificate for this user in this course run, if the user is
    eligible and a certificate can be generated.
    """
    if _can_generate_v2_certificate(user, course_key):
        return _generate_certificate_task(user, course_key, generation_mode)

    status = _set_v2_cert_status(user, course_key)
    if status is not None:
        return True

    return False


def _generate_certificate_task(user, course_key, generation_mode=None):
    """
    Create a task to generate a certificate
    """
    log.info(f'About to create a V2 certificate task for {user.id} : {course_key}')

    kwargs = {
        'student': str(user.id),
        'course_key': str(course_key),
        'v2_certificate': True
    }
    if generation_mode is not None:
        kwargs['generation_mode'] = generation_mode

    generate_certificate.apply_async(countdown=CERTIFICATE_DELAY_SECONDS, kwargs=kwargs)
    return True


def _can_generate_allowlist_certificate(user, course_key):
    """
    Check if an allowlist certificate can be generated (created if it doesn't already exist, or updated if it does
    exist) for this user, in this course run.
    """
    if not is_on_certificate_allowlist(user, course_key):
        log.info(f'{user.id} : {course_key} is not on the certificate allowlist. Allowlist certificate cannot be '
                 f'generated.')
        return False

    log.info(f'{user.id} : {course_key} is on the certificate allowlist')

    if not _can_generate_certificate_common(user, course_key):
        log.info(f'One of the common checks failed. Allowlist certificate cannot be generated for {user.id} : '
                 f'{course_key}.')
        return False

    log.info(f'Allowlist certificate can be generated for {user.id} : {course_key}')
    return True


def _can_generate_v2_certificate(user, course_key):
    """
    Check if a v2 course certificate can be generated (created if it doesn't already exist, or updated if it does
    exist) for this user, in this course run.
    """
    if not is_using_v2_course_certificates(course_key):
        # This course run is not using the v2 course certificate feature
        log.info(f'{course_key} is not using v2 course certificates. Certificate cannot be generated.')
        return False

    if _is_ccx_course(course_key):
        log.info(f'{course_key} is a CCX course. Certificate cannot be generated for {user.id}.')
        return False

    if _is_beta_tester(user, course_key):
        log.info(f'{user.id} is a beta tester in {course_key}. Certificate cannot be generated.')
        return False

    if not _has_passing_grade(user, course_key):
        log.info(f'{user.id} does not have a passing grade in {course_key}. Certificate cannot be generated.')
        return False

    if not _can_generate_certificate_common(user, course_key):
        log.info(f'One of the common checks failed. Certificate cannot be generated for {user.id} : {course_key}.')
        return False

    log.info(f'V2 certificate can be generated for {user.id} : {course_key}')
    return True


def _can_generate_certificate_common(user, course_key):
    """
    Check if a course certificate can be generated (created if it doesn't already exist, or updated if it does
    exist) for this user, in this course run.

    This method contains checks that are common to both allowlist and V2 regular course certificates.
    """
    if CertificateInvalidation.has_certificate_invalidation(user, course_key):
        # The invalidation list prevents certificate generation
        log.info(f'{user.id} : {course_key} is on the certificate invalidation list. Certificate cannot be generated.')
        return False

    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    if enrollment_mode is None:
        log.info(f'{user.id} : {course_key} does not have an enrollment. Certificate cannot be generated.')
        return False

    if not modes_api.is_eligible_for_certificate(enrollment_mode):
        log.info(f'{user.id} : {course_key} has an enrollment mode of {enrollment_mode}, which is not eligible for a '
                 f'certificate. Certificate cannot be generated.')
        return False

    if not IDVerificationService.user_is_verified(user):
        log.info(f'{user.id} does not have a verified id. Certificate cannot be generated for {course_key}.')
        return False

    if not _can_generate_certificate_for_status(user, course_key):
        return False

    course_overview = get_course_overview(course_key)
    if not has_html_certificates_enabled(course_overview):
        log.info(f'{course_key} does not have HTML certificates enabled. Certificate cannot be generated for '
                 f'{user.id}.')
        return False

    return True


def _set_allowlist_cert_status(user, course_key):
    """
    Determine the allowlist certificate status for this user, in this course run and update the cert.

    This is used when a downloadable cert cannot be generated, but we want to provide more info about why it cannot
    be generated.
    """
    if not _can_set_allowlist_cert_status(user, course_key):
        return None

    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    return _get_cert_status_common(user, course_key, cert)


def _set_v2_cert_status(user, course_key):
    """
    Determine the V2 certificate status for this user, in this course run.

    This is used when a downloadable cert cannot be generated, but we want to provide more info about why it cannot
    be generated.
    """
    if not _can_set_v2_cert_status(user, course_key):
        return None

    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    status = _get_cert_status_common(user, course_key, cert)
    if status is not None:
        return status

    course_grade = _get_course_grade(user, course_key)
    if not course_grade.passed:
        if cert is None:
            cert = GeneratedCertificate.objects.create(user=user, course_id=course_key)
        if cert.status != CertificateStatuses.notpassing:
            cert.mark_notpassing(course_grade.percent)
        return CertificateStatuses.notpassing

    return None


def _get_cert_status_common(user, course_key, cert):
    """
    Determine the certificate status for this user, in this course run.

    This is used when a downloadable cert cannot be generated, but we want to provide more info about why it cannot
    be generated.
    """
    if CertificateInvalidation.has_certificate_invalidation(user, course_key):
        if cert is None:
            cert = GeneratedCertificate.objects.create(user=user, course_id=course_key)
        if cert.status != CertificateStatuses.unavailable:
            cert.invalidate()
        return CertificateStatuses.unavailable

    if not IDVerificationService.user_is_verified(user):
        if cert is None:
            cert = GeneratedCertificate.objects.create(user=user, course_id=course_key)
        if cert.status != CertificateStatuses.unverified:
            cert.mark_unverified()
        return CertificateStatuses.unverified

    return None


def _can_set_allowlist_cert_status(user, course_key):
    """
    Determine whether we can set a custom (non-downloadable) cert status for an allowlist certificate
    """
    if not is_on_certificate_allowlist(user, course_key):
        return False

    return _can_set_cert_status_common(user, course_key)


def _can_set_v2_cert_status(user, course_key):
    """
    Determine whether we can set a custom (non-downloadable) cert status for a V2 certificate
    """
    if not is_using_v2_course_certificates(course_key):
        return False

    if _is_ccx_course(course_key):
        return False

    if _is_beta_tester(user, course_key):
        return False

    return _can_set_cert_status_common(user, course_key)


def _can_set_cert_status_common(user, course_key):
    """
    Determine whether we can set a custom (non-downloadable) cert status
    """
    if _is_cert_downloadable(user, course_key):
        return False

    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    if enrollment_mode is None:
        return False

    if not modes_api.is_eligible_for_certificate(enrollment_mode):
        return False

    course_overview = get_course_overview(course_key)
    if not has_html_certificates_enabled(course_overview):
        return False

    return True


def is_using_v2_course_certificates(course_key):
    """
    Return True if the course run is using v2 course certificates
    """
    return CERTIFICATES_USE_UPDATED.is_enabled(course_key)


def is_on_certificate_allowlist(user, course_key):
    """
    Check if the user is on the allowlist, and is enabled for the allowlist, for this course run
    """
    return CertificateWhitelist.objects.filter(user=user, course_id=course_key, whitelist=True).exists()


def _can_generate_certificate_for_status(user, course_key):
    """
    Check if the user's certificate status can handle regular (non-allowlist) certificate generation
    """
    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    if cert is None:
        return True

    if cert.status == CertificateStatuses.downloadable:
        log.info(f'Certificate with status {cert.status} already exists for {user.id} : {course_key}, and is not '
                 f'eligible for generation. Certificate cannot be generated as it is already in a final state.')
        return False

    log.info(f'Certificate with status {cert.status} already exists for {user.id} : {course_key}, and is eligible for '
             f'generation')
    return True


def _is_beta_tester(user, course_key):
    """
    Check if the user is a beta tester in this course run
    """
    beta_testers_queryset = list_with_level(course_key, 'beta')
    return beta_testers_queryset.filter(username=user.username).exists()


def _is_ccx_course(course_key):
    """
    Check if the course is a CCX (custom edX course)
    """
    return hasattr(course_key, 'ccx')


def _has_passing_grade(user, course_key):
    """
    Check if the user has a passing grade in this course run
    """
    course_grade = _get_course_grade(user, course_key)
    return course_grade.passed


def _get_course_grade(user, course_key):
    """
    Get the user's course grade in this course run
    """
    return CourseGradeFactory().read(user, course_key=course_key)


def _is_cert_downloadable(user, course_key):
    """
    Check if cert already exists, has a downloadable status, and has not been invalidated
    """
    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    if cert is None:
        return False
    if cert.status != CertificateStatuses.downloadable:
        return False
    if CertificateInvalidation.has_certificate_invalidation(user, course_key):
        return False

    return True


def generate_user_certificates(student, course_key, insecure=False, generation_mode='batch', forced_grade=None):
    """
    It will add the add-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'. It also emits
    `edx.certificate.created` event for analytics.

    This method has not yet been updated (it predates the certificates revamp). If modifying this method,
    see also generate_user_certificates() in generation.py (which is very similar but is called from a celery task).
    In the future these methods will be unified.

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        insecure - (Boolean)
        generation_mode - who has requested certificate generation. Its value should `batch`
        in case of django command and `self` if student initiated the request.
        forced_grade - a string indicating to replace grade parameter. if present grading
                       will be skipped.
    """
    if can_generate_certificate_task(student, course_key):
        # Note that this will launch an asynchronous task, and so cannot return the certificate status. This is a
        # change from the older certificate code that tries to immediately create a cert.
        log.info(f'{course_key} is using V2 certificates. Attempt will be made to regenerate a V2 certificate for user '
                 f'{student.id}.')
        return generate_certificate_task(student, course_key)

    beta_testers_queryset = list_with_level(course_key, 'beta')
    if beta_testers_queryset.filter(username=student.username):
        log.info(f"Canceling Certificate Generation task for user {student.id} : {course_key}. User is a Beta Tester.")
        return

    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False

    course_overview = get_course_overview(course_key)
    generate_pdf = not has_html_certificates_enabled(course_overview)

    cert = xqueue.add_cert(
        student,
        course_key,
        generate_pdf=generate_pdf,
        forced_grade=forced_grade
    )

    log.info(f"Queued Certificate Generation task for {student.id} : {course_key}")

    # If cert_status is not present in certificate valid_statuses (for example unverified) then
    # add_cert returns None and raises AttributeError while accessing cert attributes.
    if cert is None:
        return

    if CertificateStatuses.is_passing_status(cert.status):
        emit_certificate_event('created', student, course_key, course_overview, {
            'user_id': student.id,
            'course_id': str(course_key),
            'certificate_id': cert.verify_uuid,
            'enrollment_mode': cert.mode,
            'generation_mode': generation_mode
        })
    return cert.status


def regenerate_user_certificates(student, course_key, forced_grade=None, template_file=None, insecure=False):
    """
    Add the regen-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'.

    This method has not yet been updated (it predates the certificates revamp).

    Args:
        student (User)
        course_key (CourseKey)

    Keyword Arguments:
        grade_value - The grade string, such as "Distinction"
        template_file - The template file used to render this certificate
        insecure - (Boolean)
    """
    if can_generate_certificate_task(student, course_key):
        log.info(f"{course_key} is using V2 certificates. Attempt will be made to regenerate a V2 certificate for "
                 f"user {student.id}.")
        return generate_certificate_task(student, course_key)

    xqueue = XQueueCertInterface()
    if insecure:
        xqueue.use_https = False

    course_overview = get_course_overview(course_key)
    generate_pdf = not has_html_certificates_enabled(course_overview)
    log.info(f"Started regenerating certificates for user {student.id} in course {course_key} with generate_pdf "
             f"status: {generate_pdf}.")

    xqueue.regen_cert(
        student,
        course_key,
        forced_grade=forced_grade,
        template_file=template_file,
        generate_pdf=generate_pdf
    )
    return True
