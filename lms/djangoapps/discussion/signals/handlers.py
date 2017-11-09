"""
Signal handlers related to discussions.
"""
import logging

from django.contrib.sites.models import Site
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
    thread = comment.thread
    context = {
        'course_id': unicode(thread.course_id),
        'comment_id': comment.id,
        'comment_body': comment.body,
        'comment_author_id': comment.user_id,
        'comment_username': comment.username,
        'comment_created_at': comment.created_at,
        'site_id': Site.objects.get_current().id,
        'thread_id': thread.id,
        'thread_title': thread.title,
        'thread_username': thread.username,
        'thread_author_id': thread.user_id,
        'thread_created_at': thread.created_at,
        'thread_commentable_id': thread.commentable_id,
    }
    tasks.send_ace_message.apply_async(args=[context])
