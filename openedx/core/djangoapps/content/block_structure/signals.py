"""
Signal handlers for invalidating cached data.
"""
from django.conf import settings
from django.dispatch.dispatcher import receiver

from xmodule.modulestore.django import SignalHandler
from waffle import switch_is_active

from .api import clear_course_from_cache
from .tasks import update_course_in_cache


INVALIDATE_CACHE_ON_PUBLISH_SWITCH = 'block_structure_invalidate_cache_on_publish'


@receiver(SignalHandler.course_published)
def _listen_for_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module
    store and creates/updates the corresponding cache entry.
    """
    if switch_is_active(INVALIDATE_CACHE_ON_PUBLISH_SWITCH):
        clear_course_from_cache(course_key)

    update_course_in_cache.apply_async(
        [unicode(course_key)],
        countdown=settings.BLOCK_STRUCTURES_SETTINGS['BLOCK_STRUCTURES_COURSE_PUBLISH_TASK_DELAY'],
    )


@receiver(SignalHandler.course_deleted)
def _listen_for_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from the
    module store and invalidates the corresponding cache entry if one
    exists.
    """
    clear_course_from_cache(course_key)
