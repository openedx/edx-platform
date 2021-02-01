"""
Course certificate generation handler.

These methods check to see if a certificate can be generated (created if it does not already exist, or updated if it
exists but its state can be altered). If so, a celery task is launched to do the generation. If the certificate
cannot be generated, a message is logged and no further action is taken.

For now, these methods deal primarily with allowlist certificates, and are part of the V2 certificates revamp.
"""

import logging

from edx_toggles.toggles import LegacyWaffleFlagNamespace

from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.certificates.models import (
    CertificateStatuses,
    CertificateInvalidation,
    CertificateWhitelist,
    GeneratedCertificate
)
from lms.djangoapps.certificates.tasks import CERTIFICATE_DELAY_SECONDS, generate_certificate
from lms.djangoapps.verify_student.services import IDVerificationService
from openedx.core.djangoapps.certificates.api import auto_certificate_generation_enabled
from openedx.core.djangoapps.waffle_utils import CourseWaffleFlag

log = logging.getLogger(__name__)

WAFFLE_FLAG_NAMESPACE = LegacyWaffleFlagNamespace(name='certificates_revamp')

# .. toggle_name: certificates_revamp.use_allowlist
# .. toggle_implementation: CourseWaffleFlag
# .. toggle_default: False
# .. toggle_description: Waffle flag enable the course certificates allowlist (aka V2 of the certificate whitelist) on
#   a per-course run basis.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2021-01-27
# .. toggle_target_removal_date: 2022-01-027
# .. toggle_tickets: MICROBA-918
CERTIFICATES_USE_ALLOWLIST = CourseWaffleFlag(
    waffle_namespace=WAFFLE_FLAG_NAMESPACE,
    flag_name='use_allowlist',
    module_name=__name__,
)


def generate_allowlist_certificate_task(user, course_key):
    """
    Create a task to generate an allowlist certificate for this user in this course run.
    """
    if not can_generate_allowlist_certificate(user, course_key):
        log.info(
            'Cannot generate an allowlist certificate for {user} : {course}'.format(user=user.id, course=course_key))
        return False

    log.info(
        'About to create an allowlist certificate task for {user} : {course}'.format(user=user.id, course=course_key))

    kwargs = {
        'student': str(user.id),
        'course_key': str(course_key),
        'allowlist_certificate': True
    }
    generate_certificate.apply_async(countdown=CERTIFICATE_DELAY_SECONDS, kwargs=kwargs)
    return True


def can_generate_allowlist_certificate(user, course_key):
    """
    Check if an allowlist certificate can be generated (created if it doesn't already exist, or updated if it does
    exist) for this user, in this course run.
    """
    if not _is_using_certificate_allowlist(course_key):
        # This course run is not using the allowlist feature
        log.info(
            '{course} is not using the certificate allowlist. Certificate cannot be generated.'.format(
                course=course_key
            ))
        return False

    if not auto_certificate_generation_enabled():
        # Automatic certificate generation is globally disabled
        log.info('Automatic certificate generation is globally disabled. Certificate cannot be generated.')
        return False

    if CertificateInvalidation.has_certificate_invalidation(user, course_key):
        # The invalidation list overrides the allowlist
        log.info(
            '{user} : {course} is on the certificate invalidation list. Certificate cannot be generated.'.format(
                user=user.id,
                course=course_key
            ))
        return False

    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)
    if enrollment_mode is None:
        log.info('{user} : {course} does not have an enrollment. Certificate cannot be generated.'.format(
            user=user.id,
            course=course_key
        ))
        return False

    if not IDVerificationService.user_is_verified(user):
        log.info(
            '{user} does not have a verified id. Certificate cannot be generated.'.format(
                user=user.id
            ))
        return False

    if not _is_on_certificate_allowlist(user, course_key):
        log.info('{user} : {course} is not on the certificate allowlist. Certificate cannot be generated.'.format(
            user=user.id,
            course=course_key
        ))
        return False

    log.info('{user} : {course} is on the certificate allowlist'.format(
        user=user.id,
        course=course_key
    ))
    cert = GeneratedCertificate.certificate_for_student(user, course_key)
    return _can_generate_allowlist_certificate_for_status(cert)


def is_using_certificate_allowlist_and_is_on_allowlist(user, course_key):
    """
    Return True if both:
    1) the course run is using the allowlist, and
    2) if the user is on the allowlist for this course run
    """
    return _is_using_certificate_allowlist(course_key) and _is_on_certificate_allowlist(user, course_key)


def _is_using_certificate_allowlist(course_key):
    """
    Check if the course run is using the allowlist, aka V2 of certificate whitelisting
    """
    return CERTIFICATES_USE_ALLOWLIST.is_enabled(course_key)


def _is_on_certificate_allowlist(user, course_key):
    """
    Check if the user is on the allowlist for this course run
    """
    return CertificateWhitelist.objects.filter(user=user, course_id=course_key, whitelist=True).exists()


def _can_generate_allowlist_certificate_for_status(cert):
    """
    Check if the user's certificate status allows certificate generation
    """
    if cert is None:
        return True

    if cert.status == CertificateStatuses.downloadable:
        log.info('Certificate with status {status} already exists for {user} : {course}, and is NOT eligible for '
                 'allowlist generation. Certificate cannot be generated.'
                 .format(status=cert.status, user=cert.user.id, course=cert.course_id))
        return False

    log.info('Certificate with status {status} already exists for {user} : {course}, and is eligible for allowlist '
             'generation'
             .format(status=cert.status, user=cert.user.id, course=cert.course_id))
    return True
