"""
This file contains celery tasks for student course enrollment
"""

from celery.task import task
from student.models import CourseEnrollment
from edx_notifications.lib.publisher import bulk_publish_notification_to_users
import logging

log = logging.getLogger(__name__)


@task()
def publish_course_notifications_task(course_id, notification_msg, exclude_user_ids=None):  # pylint: disable=invalid-name
    """
    This function will call the edx_notifications api method "bulk_publish_notification_to_users"
    and run as a new Celery task.
    """
    # get the enrolled and active user_id list for this course.
    user_ids = CourseEnrollment.objects.values_list('user_id', flat=True).filter(
        is_active=1,
        course_id=course_id
    )

    try:
        bulk_publish_notification_to_users(user_ids, notification_msg, exclude_user_ids=exclude_user_ids)
    except Exception, ex:
        # Notifications are never critical, so we don't want to disrupt any
        # other logic processing. So log and continue.
        log.exception(ex)
