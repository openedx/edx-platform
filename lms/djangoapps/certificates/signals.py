""" Signal handler for enabling self-generated certificates by default
for self-paced courses.
"""
from celery.task import task
from django.dispatch.dispatcher import receiver

from certificates.models import CertificateGenerationCourseSetting
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """ Catches the signal that a course has been published in Studio and
    enable the self-generated certificates by default for self-paced
    courses.
    """
    enable_self_generated_certs.delay(unicode(course_key))


@task()
def enable_self_generated_certs(course_key):
    """Enable the self-generated certificates by default for self-paced courses."""
    course_key = CourseKey.from_string(course_key)
    course = CourseOverview.get_from_id(course_key)
    is_enabled_for_course = CertificateGenerationCourseSetting.is_enabled_for_course(course_key)
    if course.self_paced and not is_enabled_for_course:
        CertificateGenerationCourseSetting.set_enabled_for_course(course_key, True)
