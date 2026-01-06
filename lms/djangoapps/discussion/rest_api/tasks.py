"""
Contain celery tasks
"""

import logging

from celery import shared_task
from django.contrib.auth import get_user_model
from edx_django_utils.monitoring import set_code_owner_attribute
from eventtracking import tracker
from opaque_keys.edx.locator import CourseKey

from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole
from common.djangoapps.track import segment
from lms.djangoapps.courseware.courses import get_course_with_access
from lms.djangoapps.discussion.django_comment_client.utils import get_user_role_names
from lms.djangoapps.discussion.rest_api.discussions_notifications import (
    DiscussionNotificationSender,
)
from lms.djangoapps.discussion.rest_api.utils import can_user_notify_all_learners
from openedx.core.djangoapps.django_comment_common.comment_client import Comment
from openedx.core.djangoapps.django_comment_common.comment_client.thread import Thread
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS

User = get_user_model()
log = logging.getLogger(__name__)


@shared_task
@set_code_owner_attribute
def send_thread_created_notification(
    thread_id, course_key_str, user_id, notify_all_learners=False
):
    """
    Send notification when a new thread is created
    """
    course_key = CourseKey.from_string(course_key_str)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    thread = Thread(id=thread_id).retrieve()
    user = User.objects.get(id=user_id)

    if notify_all_learners:
        is_course_staff = CourseStaffRole(course_key).has_user(user)
        is_course_admin = CourseInstructorRole(course_key).has_user(user)
        user_roles = get_user_role_names(user, course_key)
        if not can_user_notify_all_learners(
            user_roles, is_course_staff, is_course_admin
        ):
            return

    course = get_course_with_access(user, "load", course_key, check_if_enrolled=True)
    notification_sender = DiscussionNotificationSender(thread, course, user)
    notification_sender.send_new_thread_created_notification(notify_all_learners)


@shared_task
@set_code_owner_attribute
def send_response_notifications(
    thread_id, course_key_str, user_id, comment_id, parent_id=None
):
    """
    Send notifications to users who are subscribed to the thread.
    """
    course_key = CourseKey.from_string(course_key_str)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    thread = Thread(id=thread_id).retrieve()
    user = User.objects.get(id=user_id)
    course = get_course_with_access(user, "load", course_key, check_if_enrolled=True)
    notification_sender = DiscussionNotificationSender(
        thread, course, user, parent_id, comment_id
    )
    notification_sender.send_new_comment_notification()
    notification_sender.send_new_response_notification()
    notification_sender.send_new_comment_on_response_notification()
    notification_sender.send_response_on_followed_post_notification()


@shared_task
@set_code_owner_attribute
def send_response_endorsed_notifications(
    thread_id, response_id, course_key_str, endorsed_by
):
    """
    Send notifications when a response is marked answered/ endorsed
    """
    course_key = CourseKey.from_string(course_key_str)
    if not ENABLE_NOTIFICATIONS.is_enabled(course_key):
        return
    thread = Thread(id=thread_id).retrieve()
    response = Comment(id=response_id).retrieve()
    creator = User.objects.get(id=response.user_id)
    endorser = User.objects.get(id=endorsed_by)
    course = get_course_with_access(creator, "load", course_key, check_if_enrolled=True)
    notification_sender = DiscussionNotificationSender(
        thread, course, creator, comment_id=response_id
    )
    # skip sending notification to author of thread if they are the same as the author of the response
    if response.user_id != thread.user_id:
        # sends notification to author of thread
        notification_sender.send_response_endorsed_on_thread_notification()
    # sends notification to author of response
    if int(response.user_id) != endorser.id:
        notification_sender.creator = User.objects.get(id=response.user_id)
        notification_sender.send_response_endorsed_notification()


@shared_task
@set_code_owner_attribute
def delete_course_post_for_user(user_id, username, course_ids, event_data=None):
    """
    Deletes all posts for user in a course.
    """
    event_data = event_data or {}
    log.info(
        f"<<Bulk Delete>> Deleting all posts for {username} in course {course_ids}"
    )
    # Get triggered_by user_id from event_data for audit trail
    deleted_by_user_id = event_data.get("triggered_by_user_id") if event_data else None
    threads_deleted = Thread.delete_user_threads(
        user_id, course_ids, deleted_by=deleted_by_user_id
    )
    comments_deleted = Comment.delete_user_comments(
        user_id, course_ids, deleted_by=deleted_by_user_id
    )
    log.info(
        f"<<Bulk Delete>> Deleted {threads_deleted} posts and {comments_deleted} comments for {username} "
        f"in course {course_ids}"
    )
    event_data.update(
        {
            "number_of_posts_deleted": threads_deleted,
            "number_of_comments_deleted": comments_deleted,
        }
    )
    event_name = "edx.discussion.bulk_delete_user_posts"
    tracker.emit(event_name, event_data)
    segment.track("None", event_name, event_data)


@shared_task
@set_code_owner_attribute
def restore_course_post_for_user(user_id, username, course_ids, event_data=None):
    """
    Restores all soft-deleted posts for user in a course by setting is_deleted=False.
    """
    event_data = event_data or {}
    log.info(
        "<<Bulk Restore>> Restoring all posts for %s in course %s", username, course_ids
    )
    # Get triggered_by user_id from event_data for audit trail
    restored_by_user_id = event_data.get("triggered_by_user_id") if event_data else None
    threads_restored = Thread.restore_user_deleted_threads(
        user_id, course_ids, restored_by=restored_by_user_id
    )
    comments_restored = Comment.restore_user_deleted_comments(
        user_id, course_ids, restored_by=restored_by_user_id
    )
    log.info(
        "<<Bulk Restore>> Restored %s posts and %s comments for %s in course %s",
        threads_restored,
        comments_restored,
        username,
        course_ids,
    )
    event_data.update(
        {
            "number_of_posts_restored": threads_restored,
            "number_of_comments_restored": comments_restored,
        }
    )
    event_name = "edx.discussion.bulk_restore_user_posts"
    tracker.emit(event_name, event_data)
    segment.track("None", event_name, event_data)
