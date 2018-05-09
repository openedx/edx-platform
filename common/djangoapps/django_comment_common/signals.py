# pylint: disable=invalid-name
"""Signals related to the comments service."""
from django.conf import settings
from django.dispatch import Signal, receiver
from opaque_keys.edx.locator import LibraryLocator
from django_comment_common import tasks
from xmodule.modulestore.django import SignalHandler


thread_created = Signal(providing_args=['user', 'post'])
thread_edited = Signal(providing_args=['user', 'post'])
thread_voted = Signal(providing_args=['user', 'post'])
thread_deleted = Signal(providing_args=['user', 'post'])
thread_followed = Signal(providing_args=['user', 'post'])
thread_unfollowed = Signal(providing_args=['user', 'post'])
comment_created = Signal(providing_args=['user', 'post'])
comment_edited = Signal(providing_args=['user', 'post'])
comment_voted = Signal(providing_args=['user', 'post'])
comment_deleted = Signal(providing_args=['user', 'post'])
comment_endorsed = Signal(providing_args=['user', 'post'])


@receiver(SignalHandler.course_published)
def update_discussions_on_course_publish(sender, course_key, **kwargs):  # pylint: disable=unused-argument
    """
    Catches the signal that a course has been published in the module
    store and creates/updates the corresponding cache entry.
    Ignores publish signals from content libraries.
    """
    if isinstance(course_key, LibraryLocator):
        return

    context = {
        'course_id': unicode(course_key),
    }
    tasks.update_discussions_map.apply_async(
        args=[context],
        countdown=settings.MODULESTORE_PUBLISH_SIGNAL_DELAY,
    )
