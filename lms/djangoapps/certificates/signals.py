"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""
from celery.task import task
from django.dispatch.dispatcher import receiver

from certificates.models import CertificateGenerationCourseSetting
from opaque_keys.edx.keys import CourseKey
from xmodule.modulestore.django import modulestore, SignalHandler


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """ Catches the signal that a course has been published in Studio and
    enable/disable the self-generated certificates according to course-pacing.
    """
    set_self_generated_certs.delay(unicode(course_key))


@task()
def set_self_generated_certs(course_key):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    course_key = CourseKey.from_string(course_key)
    course = modulestore().get_course(course_key)
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, course.self_paced)
