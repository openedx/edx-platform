"""
Helper methods for push notifications from Studio.
"""

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
            Push.alert(
                data={
                    "course-id": course_key_string,
                    "action": "course.announcement",
                    "action-loc-key": "VIEW_BUTTON",
                    "loc-key": "COURSE_ANNOUNCEMENT_NOTIFICATION_BODY",
                    "loc-args": [course_display_name],
                    "title-loc-key": "COURSE_ANNOUNCEMENT_NOTIFICATION_TITLE",
                    "title-loc-args": [],
                },
                channels=[course_subscription_id],
            )
        except ParseError as error:
            log_exception(error.message)
