"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""
import logging

from celery.task import task
from django.db.models.signals import post_save
from django.dispatch import receiver
from opaque_keys.edx.keys import CourseKey

from .config import waffle
from certificates.models import CertificateGenerationCourseSetting, CertificateWhitelist
from certificates.tasks import generate_certificate
from courseware import courses
from openedx.core.djangoapps.models.course_details import COURSE_PACING_CHANGE


log = logging.getLogger(__name__)


@receiver(post_save, sender=CertificateWhitelist, dispatch_uid="append_certificate_whitelist")
def _listen_for_certificate_whitelist_append(sender, instance, **kwargs):  # pylint: disable=unused-argument
    switches = waffle.waffle()
    # All flags enabled
    if (
        not switches.is_enabled(waffle.SELF_PACED_ONLY) and
        not switches.is_enabled(waffle.INSTRUCTOR_PACED_ONLY)
    ):
        return

    # Only SELF_PACED_ONLY flag enabled
    if not switches.is_enabled(waffle.INSTRUCTOR_PACED_ONLY):
        if not courses.get_course_by_id(instance.course_id, depth=0).self_paced:
            return

    # Only INSTRUCTOR_PACED_ONLY flag enabled
    if not switches.is_enabled(waffle.SELF_PACED_ONLY):
        if courses.get_course_by_id(instance.course_id, depth=0).self_paced:
            return

    generate_certificate.apply_async(
        student=instance.user,
        course_key=instance.course_id,
    )
    log.info(u'Certificate generation task initiated for {user} : {course} via whitelist'.format(
        user=instance.user.id,
        course=instance.course_id
    ))


@receiver(COURSE_PACING_CHANGE, dispatch_uid="course_pacing_changed")
def _listen_for_course_pacing_changed(sender, course_key, course_self_paced, **kwargs):  # pylint: disable=unused-argument
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
