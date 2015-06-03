"""
Signal handler for invalidating cached course overviews
"""

from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler
from .models import CourseOverviewDescriptor

@receiver(SignalHandler.course_published)
def listen_for_course_publish(_sender, course_key, **_kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in Studio and invalidates
    the corresponding CourseOverviewDescriptor cache entry if one exists.
    """
    # TODO me: confirm that all cache invalidations will be hit by this signal
    CourseOverviewDescriptor.objects.filter(id=course_key).delete()
