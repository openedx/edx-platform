from celery import task
from logging import getLogger

from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask

from .api import generate_user_certificates

logger = getLogger(__name__)


class _BaseCertificateTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseCertificateTask)
def generate_certificate(**kwargs):
    """
    Generates a certificate for a single user.
    """
    student = kwargs.pop('student')
    course_key = kwargs.pop('course_key')
    generate_user_certificates(student=student, course_key=course_key, **kwargs)
