"""
Notification types that will be used in common use cases for notifications around
course update announcements.
"""

from edx_notifications.data import (
    NotificationType
)
from edx_notifications.lib.publisher import register_notification_type
from edx_notifications.signals import perform_type_registrations
from edx_notifications.renderers.basic import UnderscoreStaticFileRenderer

from django.dispatch import receiver


class NewCourseAnnouncementRenderer(UnderscoreStaticFileRenderer):
    """
    Renders a new-course-announcement notification
    """
    underscore_template_name = 'course_announcements/new_announcement.underscore'


@receiver(perform_type_registrations)
def register_notification_types(sender, **kwargs):  # pylint: disable=unused-argument
    """
    Register some standard NotificationTypes.
    This will be called automatically on the Notification subsystem startup (because we are
    receiving the 'perform_type_registrations' signal)
    """

    # updates/announcements in the course use-case.
    register_notification_type(
        NotificationType(
            name='open-edx.studio.announcements.new-announcement',
            renderer='edx_notifications.openedx.course_announcements.NewCourseAnnouncementRenderer',
        )
    )
