"""
Signal handlers for invalidating cached data.
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler

from .api import clear_course_from_cache


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module
    store and invalidates the corresponding cache entry if one exists.
    """
    clear_course_from_cache(course_key)


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from the
    module store and invalidates the corresponding cache entry if one
    exists.
    """
    clear_course_from_cache(course_key)
