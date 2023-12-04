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
    USER_NOTIFICATION_REQUESTED,
    COURSE_NOTIFICATION_REQUESTED,
)

from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.notifications.audience_filters import RoleAudienceFilter, EnrollmentAudienceFilter
from openedx.core.djangoapps.notifications.config.waffle import ENABLE_NOTIFICATIONS
from openedx.core.djangoapps.notifications.models import CourseNotificationPreference

log = logging.getLogger(__name__)

AUDIENCE_FILTER_TYPES = ['role', 'enrollment']

AUDIENCE_FILTER_CLASSES = {
    'role': RoleAudienceFilter,
    'enrollment': EnrollmentAudienceFilter,
}


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
    Watches for USER_NOTIFICATION_REQUESTED signal and calls send_web_notifications task
    """
    from openedx.core.djangoapps.notifications.tasks import send_notifications
    notification_data = notification_data.__dict__
    notification_data['course_key'] = str(notification_data['course_key'])
    send_notifications.delay(**notification_data)


def calculate_course_wide_notification_audience(course_key, audience_filters):
    """
    Calculate the audience for a course-wide notification based on the audience filters
    """
    if not audience_filters:
        return CourseEnrollment.objects.filter(course_id=course_key, is_active=True).values_list('user_id', flat=True)

    audience_user_ids = []
    for filter_type, filter_values in audience_filters.items():
        if filter_type in AUDIENCE_FILTER_TYPES:
            filter_class = AUDIENCE_FILTER_CLASSES.get(filter_type)
            if filter_class:
                filter_instance = filter_class(course_key)
                filtered_users = filter_instance.filter(filter_values)
                audience_user_ids.extend(filtered_users)
        else:
            raise ValueError(f"Invalid audience filter type: {filter_type}")

    return list(set(audience_user_ids))


@receiver(COURSE_NOTIFICATION_REQUESTED)
def generate_course_notifications(signal, sender, notification_data, metadata, **kwargs):
    """
    Watches for COURSE_NOTIFICATION_REQUESTED signal and calls send_notifications task
    """
    from openedx.core.djangoapps.notifications.tasks import send_notifications
    notification_data = notification_data.__dict__
    notification_data['course_key'] = str(notification_data['course_key'])

    audience_filters = notification_data.pop('audience_filters')
    user_ids = calculate_course_wide_notification_audience(
        notification_data['course_key'],
        audience_filters,
    )
    notification_data['user_ids'] = user_ids
    notification_data['context'] = notification_data.pop('content_context')

    send_notifications.delay(**notification_data)
