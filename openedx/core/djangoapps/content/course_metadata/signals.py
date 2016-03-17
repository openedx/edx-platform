"""
This module has definition of receivers for signals
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler
from openedx.core.djangoapps.content.course_metadata.tasks import update_course_aggregate_metadata


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Receives signal and kicks off celery task to update course aggregate metadata
    """
    # Note: The countdown=0 kwarg is set to to ensure the method below does not attempt to access the course
    # before the signal emitter has finished all operations. This is also necessary to ensure all tests pass.
    update_course_aggregate_metadata.apply_async([unicode(course_key)], countdown=0)
