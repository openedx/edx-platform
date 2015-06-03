"""
This file contains receivers of course publication signals.
"""

from django.dispatch import receiver

from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """Receive 'course_published' signal and kick off a celery task to update
    the credit course requirements.
    """

    # Import here, because signal is registered at startup, but items in tasks
    # are not yet able to be loaded
    from .tasks import update_course_requirements

    update_course_requirements.delay(unicode(course_key))
