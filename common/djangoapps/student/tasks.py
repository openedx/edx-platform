"""
This file contains celery tasks for student course enrollment
"""

from celery.task import task
from student.models import CourseEnrollment
from edx_notifications.lib.publisher import bulk_publish_notification_to_users


@task()
def publish_course_notifications_task(course_id, notification_msg):  # pylint: disable=invalid-name
    """
    This function will call the edx_notifications api method "bulk_publish_notification_to_users"
    and run as a new Celery task.
    """
    # get the enrolled and active user_id list for this course.
    user_ids = CourseEnrollment.objects.values_list('user_id', flat=True).filter(
        is_active=1,
        course_id=course_id
    )
    bulk_publish_notification_to_users(user_ids, notification_msg)
