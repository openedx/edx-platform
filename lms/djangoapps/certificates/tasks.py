"""
Tasks that generate a course certificate for a user
"""

from logging import getLogger

from celery import shared_task
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.generation import (
    generate_allowlist_certificate,
    generate_course_certificate,
    generate_user_certificates
)
from lms.djangoapps.verify_student.services import IDVerificationService

log = getLogger(__name__)
User = get_user_model()
CERTIFICATE_DELAY_SECONDS = 2


@shared_task(base=LoggedPersistOnFailureTask, bind=True, default_retry_delay=30, max_retries=2)
@set_code_owner_attribute
def generate_certificate(self, **kwargs):
    """
    Generates a certificate for a single user.

    kwargs:
        - student: The student for whom to generate a certificate.
        - course_key: The course key for the course that the student is
            receiving a certificate in.
        - expected_verification_status: The expected verification status
            for the user.  When the status has changed, we double check
            that the actual verification status is as expected before
            generating a certificate, in the off chance that the database
            has not yet updated with the user's new verification status.
        - allowlist_certificate: A flag indicating whether to generate an allowlist certificate (which is V2 of
            whitelisted certificates)
        - v2_certificate: A flag indicating whether to generate a v2 course certificate
    """
    original_kwargs = kwargs.copy()
    student = User.objects.get(id=kwargs.pop('student'))
    course_key = CourseKey.from_string(kwargs.pop('course_key'))
    expected_verification_status = kwargs.pop('expected_verification_status', None)
    allowlist_certificate = kwargs.pop('allowlist_certificate', False)
    v2_certificate = kwargs.pop('v2_certificate', False)

    if allowlist_certificate:
        generate_allowlist_certificate(user=student, course_key=course_key)
        return

    if v2_certificate:
        generate_course_certificate(user=student, course_key=course_key)
        return

    if expected_verification_status:
        actual_verification_status = IDVerificationService.user_status(student)
        actual_verification_status = actual_verification_status['status']
        if expected_verification_status != actual_verification_status:
            log.warning(
                'Expected verification status {expected} '
                'differs from actual verification status {actual} '
                'for user {user} in course {course}'.format(
                    expected=expected_verification_status,
                    actual=actual_verification_status,
                    user=student.id,
                    course=course_key
                ))
            raise self.retry(kwargs=original_kwargs)
    generate_user_certificates(student=student, course_key=course_key, **kwargs)
