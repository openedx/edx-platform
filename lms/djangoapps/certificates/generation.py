"""
Course certificate generation

These methods generate course certificates (they create a new course certificate if it does not yet exist, or update the
existing cert if it does already exist).

For now, these methods deal primarily with allowlist certificates, and are part of the V2 certificates revamp.

These methods should be called from tasks.
"""

import logging
from uuid import uuid4

from common.djangoapps.student.models import CourseEnrollment, UserProfile
from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.models import GeneratedCertificate
from lms.djangoapps.certificates.utils import emit_certificate_event
from lms.djangoapps.grades.api import CourseGradeFactory

log = logging.getLogger(__name__)


def generate_course_certificate(user, course_key, status, generation_mode):
    """
    Generate a course certificate for this user, in this course run. If the certificate has a passing status, also emit
    a certificate event.

    Note that the certificate could be either an allowlist certificate or a "regular" course certificate; the content
    will be the same either way.

    Args:
        user: user for whom to generate a certificate
        course_key: course run key for which to generate a certificate
        status: certificate status (value from the CertificateStatuses model)
        generation_mode: Used when emitting an events. Options are "self" (implying the user generated the cert
            themself) and "batch" for everything else.
    """
    cert = _generate_certificate(user, course_key, status)

    if CertificateStatuses.is_passing_status(cert.status):
        # Emit a certificate event
        event_data = {
            'user_id': user.id,
            'course_id': str(course_key),
            'certificate_id': cert.verify_uuid,
            'enrollment_mode': cert.mode,
            'generation_mode': generation_mode
        }
        emit_certificate_event(event_name='created', user=user, course_id=course_key, event_data=event_data)

    elif CertificateStatuses.unverified == cert.status:
        cert.mark_unverified(source='certificate_generation')

    return cert


def _generate_certificate(user, course_key, status):
    """
    Generate a certificate for this user, in this course run.
    """
    # Retrieve the existing certificate for the learner if it exists
    existing_certificate = GeneratedCertificate.certificate_for_student(user, course_key)

    profile = UserProfile.objects.get(user=user)
    profile_name = profile.name

    course_grade = CourseGradeFactory().read(user, course_key=course_key)
    enrollment_mode, __ = CourseEnrollment.enrollment_mode_for_user(user, course_key)

    # Retain the `verify_uuid` from an existing certificate if possible, this will make it possible for the learner to
    # keep the existing URL to their certificate
    if existing_certificate and existing_certificate.verify_uuid:
        uuid = existing_certificate.verify_uuid
    else:
        uuid = uuid4().hex

    cert, created = GeneratedCertificate.objects.update_or_create(
        user=user,
        course_id=course_key,
        defaults={
            'user': user,
            'course_id': course_key,
            'mode': enrollment_mode,
            'name': profile_name,
            'status': status,
            'grade': course_grade.percent,
            'download_url': '',
            'key': '',
            'verify_uuid': uuid,
            'error_reason': ''
        }
    )

    if created:
        created_msg = 'Certificate was created.'
    else:
        created_msg = 'Certificate already existed and was updated.'
    log.info(f'Generated certificate with status {cert.status} for {user.id} : {course_key}. {created_msg}')
    return cert
