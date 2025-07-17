"""Policies for the notifications app."""

from edx_ace.channel import ChannelType
from edx_ace.policy import Policy, PolicyResult
from opaque_keys.edx.keys import CourseKey

from .models import CourseNotificationPreference


class CoursePushNotificationOptout(Policy):
    """
    Course Push Notification optOut Policy.
    """

    def check(self, message):
        """
        Check if the user has opted out of push notifications for the given course.
        :param message:
        :return: PolicyResult
        """
        course_ids = message.context.get('course_ids', [])
        app_label = message.context.get('app_label')

        if not (app_label or message.context.get('push_notification_extra_context', {})):
            return PolicyResult(deny={ChannelType.PUSH})

        course_keys = [CourseKey.from_string(course_id) for course_id in course_ids]
        for course_key in course_keys:
            course_notification_preference = CourseNotificationPreference.get_user_course_preference(
                message.recipient.lms_user_id,
                course_key
            )
            push_notification_preference = course_notification_preference.get_notification_type_config(
                app_label,
                notification_type='push',
            ).get('push', False)

            if not push_notification_preference:
                return PolicyResult(deny={ChannelType.PUSH})

        return PolicyResult(deny=frozenset())
