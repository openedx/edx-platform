from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler
from .models import CourseOverviewDescriptor

@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """Invalidates the CourseOverviewDescriptor cache entry for a course whenever it is modified."""

    # TODO me: confirm that all cache invalidations will be hit by this signal
    CourseOverviewDescriptor.objects.filter(id=course_key).delete()
