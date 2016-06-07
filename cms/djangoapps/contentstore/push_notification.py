"""
Helper methods for push notifications from Studio.
"""

from uuid import uuid4
from django.conf import settings
from logging import exception as log_exception

from contentstore.tasks import push_course_update_task
from contentstore.models import PushNotificationConfig
from xmodule.modulestore.django import modulestore
from parse_rest.installation import Push
from parse_rest.connection import register
from parse_rest.core import ParseError


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
    if settings.PARSE_KEYS:
        try:
            register(
                settings.PARSE_KEYS["APPLICATION_ID"],
                settings.PARSE_KEYS["REST_API_KEY"],
            )
            push_payload = {
                "action": "course.announcement",
                "notification-id": unicode(uuid4()),

                "course-id": course_key_string,
                "course-name": course_display_name,
            }
            push_channels = [course_subscription_id]

            # Push to all Android devices
            Push.alert(
                data=push_payload,
                channels={"$in": push_channels},
                where={"deviceType": "android"},
            )

            # Push to all iOS devices
            # With additional payload so that
            # 1. The push is displayed automatically
            # 2. The app gets it even in the background.
            # See http://stackoverflow.com/questions/19239737/silent-push-notification-in-ios-7-does-not-work
            push_payload.update({
                "alert": "",
                "content-available": 1
            })
            Push.alert(
                data=push_payload,
                channels={"$in": push_channels},
                where={"deviceType": "ios"},
            )

        except ParseError as error:
            log_exception(error.message)
