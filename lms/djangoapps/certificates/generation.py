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
from lms.djangoapps.certificates.models import CertificateStatuses, GeneratedCertificate
from lms.djangoapps.certificates.queue import XQueueCertInterface
from lms.djangoapps.certificates.utils import emit_certificate_event, has_html_certificates_enabled
from lms.djangoapps.grades.api import CourseGradeFactory
from lms.djangoapps.instructor.access import list_with_level
from openedx.core.djangoapps.content.course_overviews.api import get_course_overview

log = logging.getLogger(__name__)


def generate_course_certificate(user, course_key, generation_mode):
    """
    Generate a course certificate for this user, in this course run. If the certificate has a passing status, also emit
    a certificate event.

    Note that the certificate could be either an allowlist certificate or a "regular" course certificate; the content
    will be the same either way.

    Args:
        user: user for whom to generate a certificate
        course_key: course run key for which to generate a certificate
        generation_mode: Used when emitting an events. Options are "self" (implying the user generated the cert
            themself) and "batch" for everything else.
    """
    cert = _generate_certificate(user, course_key)

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

    return cert


def _generate_certificate(user, course_key):
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
            'status': CertificateStatuses.downloadable,
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


def generate_user_certificates(student, course_key, insecure=False, generation_mode='batch', forced_grade=None):
    """
    It will add the add-cert request into the xqueue.

    A new record will be created to track the certificate
    generation task.  If an error occurs while adding the certificate
    to the queue, the task will have status 'error'. It also emits
    `edx.certificate.created` event for analytics.

    This method has not yet been updated (it predates the certificates revamp). If modifying this method,
    see also generate_user_certificates() in generation_handler.py (which is very similar but is not called from a
    celery task). In the future these methods will be unified.

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
