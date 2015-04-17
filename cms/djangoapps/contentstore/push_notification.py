"""
Helper methods for push notifications from Studio.
"""

from django.conf import settings
from logging import exception as log_exception

from contentstore.tasks import push_course_update_task
from contentstore.models import PushNotificationConfig
from xmodule.modulestore.django import modulestore


# define a msg_type name that will be used in edx-notifications
# we put it in a open-edx.mobile.* namespace so
# we can do feature wildcarding for particular
# routing of messages or other types of group behaviors
COURSE_UPDATE_NOTIFICATION_TYPE_NAME = 'open-edx.mobile.course-update'

def push_notification_enabled():
    """
    Returns whether the push notification feature is enabled.
    """
    return PushNotificationConfig.is_enabled()


def enqueue_push_course_update(update, course_key):
    """
    Enqueues a task for push notification for the given update for the given course if
      (1) the feature is enabled and
      (2) push_notification is selected for the update
    """
    if push_notification_enabled() and update.get("push_notification_selected"):
        course = modulestore().get_course(course_key)
        if course:
            push_course_update_task.delay(
                unicode(course_key),
                course.clean_id(padding_char='_'),
                course.display_name
            )


def send_push_course_update(course_key_string, course_subscription_id, course_display_name):
    """
    Sends a push notification for a course update, given the course's subscription_id and display_name.
    """

    # Note there is an impedence mismatch
    # as edx-notifications assumes that it is behind
    # a feature flag as opposed to a DB-backed
    # feature setting
    if settings.FEATURES.get('ENABLE_NOTIFICATIONS', False):

        # I believe the pattern is now to import optionally
        # installed sub-systems underneath the feature flag check
        from edx_notifications.channels.parse_push import ParsePushNotificationChannelProvider
        from edx_notifications.exceptions import ChannelError

        try:
            # call into a helper classmethod on ParsePushNotificationChannelProvider
            # which hides some of the internals of edx-notifications system
            # and reduces the code clutter up at the App-tier
            ParsePushNotificationChannelProvider.publish_notification(
                namespace=course_key_string,
                msg_type_name=COURSE_UPDATE_NOTIFICATION_TYPE_NAME,
                # this is what gets transfered ultimately to
                # the mobile client
                payload={
                    "course-id": course_key_string,
                    "action": "course.announcement",
                    "action-loc-key": "VIEW_BUTTON",
                    "loc-key": "COURSE_ANNOUNCEMENT_NOTIFICATION_BODY",
                    "loc-args": [course_display_name],
                    "title-loc-key": "COURSE_ANNOUNCEMENT_NOTIFICATION_TITLE",
                    "title-loc-args": [],
                },
                parse_channel_ids=[course_subscription_id]
            )
        except ChannelError as error:
            log_exception(error.message)
