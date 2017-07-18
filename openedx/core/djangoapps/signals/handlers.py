"""
This module contains all general use or cross-use handlers.
"""
import logging

from celery.task import task
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


@task
def toggle_self_generated_certs(course_key, course_self_paced):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    course_key = CourseKey.from_string(course_key)
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, course_self_paced)
