"""
Signal handler for removing the course.
"""
from django.dispatch.dispatcher import receiver
from xmodule.modulestore.django import SignalHandler


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from Studio and
    removes CCX data and ES indexes.
    """
    # Import tasks here to avoid a circular import.
    from .tasks import course_delete
    course_delete.delay(unicode(course_key))


@receiver(SignalHandler.course_published)
def on_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Will receive a delegated 'course_published' signal
    and kick off a celery task to update the course access structure.
    """
    # prevent from circular import
    from .tasks import update_course_access

    update_course_access.delay(unicode(course_key))
