"""
Signal handler for invalidating cached courses.
"""
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler

from .block_cache_operations import clear_course_from_block_cache

@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module store and
    invalidates the corresponding cache entry if one exists.
    """
    clear_course_from_block_cache(course_key)
