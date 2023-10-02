"""
Contain celery tasks
"""
from celery import shared_task
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from opaque_keys.edx.locator import CourseKey
from lms.djangoapps.courseware.courses import get_course_with_access
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from lms.djangoapps.discussion.rest_api.utils import DiscussionNotificationSender


User = get_user_model()


@shared_task
@set_code_owner_attribute
def send_thread_created_notification(thread_id, course_key_str, user_id):
    """
    Send notification when a new thread is created
    """
    course_key = CourseKey.from_string(course_key_str)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    thread = Thread(id=thread_id).retrieve()
    user = User.objects.get(id=user_id)
    course = get_course_with_access(user, 'load', course_key, check_if_enrolled=True)
    notification_sender = DiscussionNotificationSender(thread, course, user)
    notification_sender.send_new_thread_created_notification()


@shared_task
@set_code_owner_attribute
def send_response_notifications(thread_id, course_key_str, user_id, parent_id=None):
    """
    Send notifications to users who are subscribed to the thread.
    """
    course_key = CourseKey.from_string(course_key_str)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    thread = Thread(id=thread_id).retrieve()
    user = User.objects.get(id=user_id)
    course = get_course_with_access(user, 'load', course_key, check_if_enrolled=True)
    notification_sender = DiscussionNotificationSender(thread, course, user, parent_id)
    notification_sender.send_new_comment_notification()
    notification_sender.send_new_response_notification()
    notification_sender.send_new_comment_on_response_notification()
