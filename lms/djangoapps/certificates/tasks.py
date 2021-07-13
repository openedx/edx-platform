"""
Tasks that generate a course certificate for a user
"""

from logging import getLogger

from celery import shared_task
from celery_utils.persist_on_failure import LoggedPersistOnFailureTask
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.keys import CourseKey

from lms.djangoapps.certificates.data import CertificateStatuses
from lms.djangoapps.certificates.generation import generate_course_certificate

log = getLogger(__name__)
User = get_user_model()
CERTIFICATE_DELAY_SECONDS = 2


@shared_task(base=LoggedPersistOnFailureTask, bind=True, default_retry_delay=30, max_retries=2)
@set_code_owner_attribute
def generate_certificate(self, **kwargs):  # pylint: disable=unused-argument
    """
    Generates a certificate for a single user.

    kwargs:
        - student: The student for whom to generate a certificate.
        - course_key: The course key for the course that the student is
            receiving a certificate in.
        - status: Certificate status (value from the CertificateStatuses model)
        - generation_mode: Used when emitting an event. Options are "self" (implying the user generated the cert
            themself) and "batch" for everything else.
    """
    student = User.objects.get(id=kwargs.pop('student'))
    course_key = CourseKey.from_string(kwargs.pop('course_key'))
    status = kwargs.pop('status', CertificateStatuses.downloadable)
    generation_mode = kwargs.pop('generation_mode', 'batch')

    generate_course_certificate(user=student, course_key=course_key, status=status, generation_mode=generation_mode)
