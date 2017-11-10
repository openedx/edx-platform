"""
Notification types that will be used in common use cases for notifications around
discussion forums
"""

from edx_notifications.data import (
    NotificationType
)
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations
from edx_notifications.renderers.basic import UnderscoreStaticFileRenderer

from django.dispatch import receiver


class ReplyToThreadRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a reply-to-thread notification
    """
    underscore_template_name = 'forums/reply_to_thread.underscore'


class ThreadFollowedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a thread-followed notification
    """
    underscore_template_name = 'forums/thread_followed.underscore'


class PostUpvotedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a post-upvoted notification
    """
    underscore_template_name = 'forums/post_upvoted.underscore'


class CommentUpvotedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a post-upvoted notification
    """
    underscore_template_name = 'forums/comment_upvoted.underscore'


class CohortedThreadAddedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a post-upvoted notification
    """
    underscore_template_name = 'forums/cohorted_thread_added.underscore'


class CohortedCommentAddedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a post-upvoted notification
    """
    underscore_template_name = 'forums/cohorted_comment_added.underscore'


class PostFlaggedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a discussion form flagged notification
    """
    underscore_template_name = 'forums/post_flagged.underscore'


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register some standard NotificationTypes.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_type_registrations' signal)
    """

    # someone replying to thread use-case
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.reply-to-thread',
            renderer='edx_notifications.openedx.forums.ReplyToThreadRenderer',
        )
    )

    # someone following the thread use-case
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.thread-followed',
            renderer='edx_notifications.openedx.forums.ThreadFollowedRenderer',
        )
    )

    # new posting in a cohorted/private discussion in the course use-case.
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.cohorted-thread-added',
            renderer='edx_notifications.openedx.forums.CohortedThreadAddedRenderer',
        )
    )

    # new posting in a cohorted/private discussion in the course use-case.
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.cohorted-comment-added',
            renderer='edx_notifications.openedx.forums.CohortedCommentAddedRenderer',
        )
    )

    # someone voting the thread use-case
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.post-upvoted',
            renderer='edx_notifications.openedx.forums.PostUpvotedRenderer',
        )
    )

    # someone voting the comment use-case
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.comment-upvoted',
            renderer='edx_notifications.openedx.forums.CommentUpvotedRenderer',
        )
    )

    # someone flagging a post use-case
    register_notification_type(
        NotificationType(
            name='open-edx.lms.discussions.post-flagged',
            renderer='edx_notifications.openedx.forums.PostFlaggedRenderer',
        )
    )
