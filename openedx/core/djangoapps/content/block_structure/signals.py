"""
Signal handlers for invalidating cached data.
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler

from .tasks import update_course_in_cache, clear_course_from_cache


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module
    store and creates/updates the corresponding cache entry.
    """
    update_course_in_cache.apply_async([unicode(course_key)], {'desired_queue_env': 'lms'}, countdown=0)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from the
    module store and invalidates the corresponding cache entry if one
    exists.
    """
    clear_course_from_cache.apply_async([unicode(course_key)], {'desired_queue_env': 'lms'}, countdown=0)
