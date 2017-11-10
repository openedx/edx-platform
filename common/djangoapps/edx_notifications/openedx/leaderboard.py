"""
Notification types that will be used in common use cases for notifications around
Leaderboards
"""

from edx_notifications.data import (
    NotificationType
)
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations
from edx_notifications.renderers.basic import UnderscoreStaticFileRenderer

from django.dispatch import receiver


class LeaderboardRankChangedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a notification when ranking in the progress leaderboard changes
    """
    underscore_template_name = 'leaderboard/rank_changed.underscore'


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register some standard NotificationTypes.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_type_registrations' signal)
    """

    register_notification_type(
        NotificationType(
            name=u'open-edx.lms.leaderboard.progress.rank-changed',
            renderer='edx_notifications.openedx.leaderboard.LeaderboardRankChangedRenderer',
        )
    )

    register_notification_type(
        NotificationType(
            name=u'open-edx.lms.leaderboard.gradebook.rank-changed',
            renderer='edx_notifications.openedx.leaderboard.LeaderboardRankChangedRenderer',
        )
    )

    register_notification_type(
        NotificationType(
            name=u'open-edx.lms.leaderboard.engagement.rank-changed',
            renderer='edx_notifications.openedx.leaderboard.LeaderboardRankChangedRenderer',
        )
    )
