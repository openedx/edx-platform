"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""
from celery.task import task
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey

from certificates.models import CertificateGenerationCourseSetting
from openedx.core.djangoapps.models.course_details import COURSE_PACING_CHANGE


@receiver(COURSE_PACING_CHANGE, dispatch_uid="course_pacing_changed")
def _listen_for_course_publish(sender, course_key, course_self_paced, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that course pacing has changed and enable/disable
    the self-generated certificates according to course-pacing.
    """
    toggle_self_generated_certs.delay(unicode(course_key), course_self_paced)


@task()
def toggle_self_generated_certs(course_key, course_self_paced):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    course_key = CourseKey.from_string(course_key)
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, course_self_paced)
