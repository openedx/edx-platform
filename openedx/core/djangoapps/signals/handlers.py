"""
This module contains all general use or cross-use handlers.
"""
import logging

from celery.task import task
from celery_utils.logged_task import LoggedTask
from celery_utils.persist_on_failure import PersistOnFailureTask
from django.dispatch import receiver

from certificates.models import CertificateGenerationCourseSetting
from opaque_keys.edx.keys import CourseKey
from signals import COURSE_PACING_CHANGE

log = logging.getLogger(__name__)


@receiver(COURSE_PACING_CHANGE, dispatch_uid="course_pacing_changed")
def _listen_for_course_pacing_changed(sender, course_key, course_self_paced, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    toggle_self_generated_certs.delay(unicode(course_key), course_self_paced)
    log.info(u'Certificate Generation Setting Toggled for {course} via pacing change'.format(
        course=course_key
    ))


class _BaseSelfCertTask(PersistOnFailureTask, LoggedTask):  # pylint: disable=abstract-method
    """
    Include persistence features, as well as logging of task invocation.
    """
    abstract = True


@task(base=_BaseSelfCertTask)
def toggle_self_generated_certs(course_key, course_self_paced):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    course_key = CourseKey.from_string(course_key)
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, course_self_paced)
