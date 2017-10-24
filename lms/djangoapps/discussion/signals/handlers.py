"""
Signal handlers related to discussions.
"""
import logging

from django.dispatch import receiver

from django_comment_common import signals
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS
from lms.djangoapps.discussion import tasks


log = logging.getLogger(__name__)


@receiver(signals.comment_created)
def send_discussion_email_notification(sender, user, post, **kwargs):
    if waffle().is_enabled(FORUM_RESPONSE_NOTIFICATIONS):
        send_message(post)


def send_message(comment):
    """
    TODO: https://openedx.atlassian.net/browse/EDUCATOR-1572
    """
    kwargs = {
        'comment_id': comment.id,
        'comment_body': comment.body,
        'comment_user_id': comment.user_id,
        'comment_username': comment.username,
        'comment_created_at': comment.created_at,
    }
    thread = comment.thread
    kwargs.update({
        'thread_id': thread.id,
        'thread_title': thread.title,
        'thread_course_id': thread.course_id,
        'thread_username': thread.username,
        'thread_user_id': thread.user_id,
        'thread_created_at': thread.created_at
    })
    log.info('Sending forum comment notification for thread %s with kwargs %s', thread.id, kwargs)
    # tasks.send_ace_message.apply_async(kwargs=kwargs)
