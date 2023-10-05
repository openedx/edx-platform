"""
Handlers for notifications
"""
import logging

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.dispatch import receiver
from openedx_events.learning.signals import (
    COURSE_ENROLLMENT_CREATED,
    COURSE_UNENROLLMENT_COMPLETED,
    USER_NOTIFICATION_REQUESTED
)

from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference

log = logging.getLogger(__name__)


@receiver(COURSE_ENROLLMENT_CREATED)
def course_enrollment_post_save(signal, sender, enrollment, metadata, **kwargs):
    """
    Watches for post_save signal for creates on the CourseEnrollment table.
    Generate a CourseNotificationPreference if new Enrollment is created
    """
    if ENABLE_NOTIFICATIONS.is_enabled(enrollment.course.course_key):
        try:
            with transaction.atomic():
                CourseNotificationPreference.objects.create(
                    user_id=enrollment.user.id,
                    course_id=enrollment.course.course_key
                )
        except IntegrityError:
            log.info(f'CourseNotificationPreference already exists for user {enrollment.user.id} '
                     f'and course {enrollment.course.course_key}')


@receiver(COURSE_UNENROLLMENT_COMPLETED)
def on_user_course_unenrollment(enrollment, **kwargs):
    """
    Removes user notification preference when user un-enrolls from the course
    """
    try:
        user_id = enrollment.user.id
        course_key = enrollment.course.course_key
        preference = CourseNotificationPreference.objects.get(user__id=user_id, course_id=course_key)
        preference.delete()
    except ObjectDoesNotExist:
        log.info(f'Notification Preference does not exist for {enrollment.user.pii.username} in {course_key}')


@receiver(USER_NOTIFICATION_REQUESTED)
def generate_user_notifications(signal, sender, notification_data, metadata, **kwargs):
    """
    Watches for USER_NOTIFICATION_REQUESTED signal and calls  send_web_notifications task
    """
    from openedx.core.djangoapps.notifications.tasks import send_notifications
    notification_data = notification_data.__dict__
    notification_data['course_key'] = str(notification_data['course_key'])
    send_notifications.delay(**notification_data)
