"""
Signal handlers for the CourseGraph application
"""
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler

from openedx.core.djangoapps.coursegraph.utils import CourseLastPublishedCache


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Register when the course was published on a course publish event
    """
    CourseLastPublishedCache().set(course_key)
