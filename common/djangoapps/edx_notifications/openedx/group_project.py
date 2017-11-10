"""
Notification types that will be used in common use cases for notifications around
Group Projects
"""

from edx_notifications.data import (
    NotificationType
)
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations
from edx_notifications.renderers.basic import UnderscoreStaticFileRenderer

from django.dispatch import receiver

GROUP_PROJECT_V1_NOTIFICATION_PREFIX = u'open-edx.xblock.group-project'
GROUP_PROJECT_V2_NOTIFICATION_PREFIX = u'open-edx.xblock.group-project-v2'

GROUP_PROJECT_RENDERER_PREFIX = 'edx_notifications.openedx.group_project'


class NotificationMessageTypes(object):
    """
    Message type constants
    """
    STAGE_OPEN = u'stage-open'
    STAGE_DUE = u'stage-due'
    FILE_UPLOADED = u'file-uploaded'
    GRADES_POSTED = u'grades-posted'


class GroupProjectFileUploadedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a notification when ranking in the progress leaderboard changes
    """
    underscore_template_name = 'group_project/file_uploaded.underscore'


class GroupProjectStageDueRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a notification when ranking in the progress leaderboard changes
    """
    underscore_template_name = 'group_project/stage_due.underscore'


class GroupProjectStageOpenRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a notification when ranking in the progress leaderboard changes
    """
    underscore_template_name = 'group_project/stage_open.underscore'


class GroupProjectGradesPostedRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a notification when ranking in the progress leaderboard changes
    """
    underscore_template_name = 'group_project/grades_posted.underscore'


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register some standard NotificationTypes.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_type_registrations' signal)
    """
    mapping = {
        NotificationMessageTypes.FILE_UPLOADED: 'GroupProjectFileUploadedRenderer',
        NotificationMessageTypes.STAGE_OPEN: 'GroupProjectStageOpenRenderer',
        NotificationMessageTypes.STAGE_DUE: 'GroupProjectStageDueRenderer',
        NotificationMessageTypes.GRADES_POSTED: 'GroupProjectGradesPostedRenderer',
    }

    for message_type, renderer in mapping.iteritems():
        register_notification_type(
            NotificationType(
                name=u"{prefix}.{type}".format(prefix=GROUP_PROJECT_V1_NOTIFICATION_PREFIX, type=message_type),
                renderer="{prefix}.{renderer}".format(prefix=GROUP_PROJECT_RENDERER_PREFIX, renderer=renderer),
            )
        )

        # GP v2 can reuse GP v1 renderers
        register_notification_type(
            NotificationType(
                name=u"{prefix}.{type}".format(prefix=GROUP_PROJECT_V2_NOTIFICATION_PREFIX, type=message_type),
                renderer="{prefix}.{renderer}".format(prefix=GROUP_PROJECT_RENDERER_PREFIX, renderer=renderer),
            )
        )
