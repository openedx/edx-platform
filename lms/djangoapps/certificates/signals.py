"""
Signal handler for enabling/disabling self-generated certificates based on the course-pacing.
"""
from celery.task import task
from django.dispatch.dispatcher import receiver

from certificates.models import CertificateGenerationCourseSetting
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview, COURSE_OVERVIEW_UPDATED
from opaque_keys.edx.keys import CourseKey


@receiver(COURSE_OVERVIEW_UPDATED)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """ Catches the signal that a course overview table has been updated in database and
    enable/disable the self-generated certificates according to course-pacing.
    """
    set_self_generated_certs.delay(unicode(course_key))


@task()
def set_self_generated_certs(course_key):
    """
    Enable or disable self-generated certificates for a course according to pacing.
    """
    course_key = CourseKey.from_string(course_key)
    course = CourseOverview.get_from_id(course_key)
    CertificateGenerationCourseSetting.set_enabled_for_course(course_key, course.self_paced)
