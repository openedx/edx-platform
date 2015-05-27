from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler
from .models import CourseOverviewFields

@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    # TODO me: confirm that all cache invalidations will be hit by this signal
    CourseOverviewFields.objects.filter(id=course_key).delete()
