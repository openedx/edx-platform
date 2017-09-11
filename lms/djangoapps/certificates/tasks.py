from celery import task
from logging import getLogger

from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask
from django.contrib.auth.models import User
from lms.djangoapps.verify_student.models import SoftwareSecurePhotoVerification
from opaque_keys.edx.keys import CourseKey

from .api import generate_user_certificates

logger = getLogger(__name__)


class _BaseCertificateTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseCertificateTask, bind=True, default_retry_delay=30, max_retries=1)
def generate_certificate(self, **kwargs):
    """
    Generates a certificate for a single user.
    """
    student = User.objects.get(id=kwargs.pop('student'))
    course_key = CourseKey.from_string(kwargs.pop('course_key'))
    expected_verification_status = kwargs.pop('verification', None)
    if expected_verification_status:
        actual_verification_status = list(SoftwareSecurePhotoVerification.objects.get(student=student))[0]
        if expected_verification_status != actual_verification_status:
            self.retry(kwargs=kwargs)
    generate_user_certificates(student=student, course_key=course_key, **kwargs)
