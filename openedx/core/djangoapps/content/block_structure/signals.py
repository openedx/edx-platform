"""
Signal handlers for invalidating cached data.
"""

import logging

import six
from django.conf import settings
from django.dispatch.dispatcher import receiver
from opaque_keys.edx.locator import LibraryLocator

from xmodule.modulestore.django import SignalHandler

from . import config
from .api import clear_course_from_cache
from .models import BlockStructureNotFound
from .tasks import update_course_in_cache_v2

log = logging.getLogger(__name__)


@receiver(SignalHandler.course_published)
def update_block_structure_on_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module
    store and creates/updates the corresponding cache entry.
    Ignores publish signals from content libraries.
    """
    if isinstance(course_key, LibraryLocator):
        return

    if config.waffle().is_enabled(config.INVALIDATE_CACHE_ON_PUBLISH):
        try:
            clear_course_from_cache(course_key)
        except BlockStructureNotFound:
            log.warning(
                u"BlockStructure: %s not found when trying to clear course from cache",
                course_key,
            )

    update_course_in_cache_v2.apply_async(
        kwargs=dict(course_id=six.text_type(course_key)),
        countdown=settings.BLOCK_STRUCTURES_SETTINGS['COURSE_PUBLISH_TASK_DELAY'],
    )


@receiver(SignalHandler.course_deleted)
def _delete_block_structure_on_course_delete(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been deleted from the
    module store and invalidates the corresponding cache entry if one
    exists.
    """
    clear_course_from_cache(course_key)
