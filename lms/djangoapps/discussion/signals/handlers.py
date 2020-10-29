"""
Signal handlers related to discussions.
"""


import logging

import six
from django.conf import settings
from django.dispatch import receiver
from opaque_keys.edx.locator import LibraryLocator

from lms.djangoapps.discussion import tasks
from openedx.core.djangoapps.django_comment_common import signals
from openedx.core.djangoapps.site_configuration.models import SiteConfiguration
from openedx.core.djangoapps.theming.helpers import get_current_site
from xmodule.modulestore.django import SignalHandler

log = logging.getLogger(__name__)


ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY = 'enable_forum_notifications'


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
        'course_id': six.text_type(course_key),
    }
    tasks.update_discussions_map.apply_async(
        args=[context],
        countdown=settings.DISCUSSION_SETTINGS['COURSE_PUBLISH_TASK_DELAY'],
    )


@receiver(signals.comment_created)
def send_discussion_email_notification(sender, user, post, **kwargs):
    current_site = get_current_site()
    if current_site is None:
        log.info(u'Discussion: No current site, not sending notification about post: %s.', post.id)
        return

    try:
        if not current_site.configuration.get_value(ENABLE_FORUM_NOTIFICATIONS_FOR_SITE_KEY, False):
            log_message = u'Discussion: notifications not enabled for site: %s. Not sending message about post: %s.'
            log.info(log_message, current_site, post.id)
            return
    except SiteConfiguration.DoesNotExist:
        log_message = u'Discussion: No SiteConfiguration for site %s. Not sending message about post: %s.'
        log.info(log_message, current_site, post.id)
        return

    send_message(post, current_site)


def send_message(comment, site):
    thread = comment.thread
    context = {
        'course_id': six.text_type(thread.course_id),
        'comment_id': comment.id,
        'comment_body': comment.body,
        'comment_author_id': comment.user_id,
        'comment_created_at': comment.created_at,  # comment_client models dates are already serialized
        'thread_id': thread.id,
        'thread_title': thread.title,
        'thread_author_id': thread.user_id,
        'thread_created_at': thread.created_at,  # comment_client models dates are already serialized
        'thread_commentable_id': thread.commentable_id,
        'site_id': site.id
    }
    tasks.send_ace_message.apply_async(args=[context])
