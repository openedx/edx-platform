from django.dispatch import receiver
from six import text_type
from xmodule.modulestore.django import SignalHandler, modulestore

from .models import Unit


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):
    course = modulestore().get_course(course_key)
    if course:
        Unit.objects.get_or_create(course_key=course_key)
