"""
Signal handlers related to discussions.
"""
import logging

from django.dispatch import receiver

from django_comment_common import signals
from lms.djangoapps.discussion.config.waffle import waffle, FORUM_RESPONSE_NOTIFICATIONS


log = logging.getLogger(__name__)


@receiver(signals.comment_created)
def send_discussion_email_notification(sender, user, post, **kwargs):
    if waffle().is_enabled(FORUM_RESPONSE_NOTIFICATIONS):
        send_message(post)


def send_message(post):
    """
    TODO: https://openedx.atlassian.net/browse/EDUCATOR-1572
    """
    log.info('Sending message about thread %s', post.thread_id)
