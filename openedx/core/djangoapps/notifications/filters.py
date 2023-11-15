"""
Notification filters
"""
import logging

from django.utils import timezone

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from openedx.core.djangoapps.course_date_signals.utils import get_expected_duration
from openedx.core.djangoapps.notifications.base_notification import COURSE_NOTIFICATION_TYPES
from openedx.features.course_duration_limits.models import CourseDurationLimitConfig
from xmodule.modulestore.django import modulestore

logger = logging.getLogger(__name__)


class NotificationFilter:
    """
    Filter notifications based on their type
    """

    @staticmethod
    def filter_audit_expired(user_ids, course) -> list:
        """
        Check if the user has access to the course
        """
        verified_mode = CourseMode.verified_mode_for_course(course=course, include_expired=True)
        access_duration = get_expected_duration(course.id)
        course_time_limit = CourseDurationLimitConfig.current(course_key=course.id)
        if not verified_mode:
            logger.info(
                "NotificationFilter: Course %s does not have a verified mode, so no users will be filtered out",
                course.id,
            )
            return user_ids
        enrollments = CourseEnrollment.objects.filter(
            user_id__in=user_ids,
            course_id=course.id,
            mode=CourseMode.AUDIT,
        )
        if course_time_limit.enabled_for_course(course.id):
            enrollments = enrollments.filter(created__gte=course_time_limit.enabled_as_of)
        logger.info("NotificationFilter: Number of audit enrollments for course %s: %s", course.id, enrollments.count())
        for enrollment in enrollments:
            content_availability_date = max(enrollment.created, course.start)
            expiration_date = content_availability_date + access_duration
            logger.info("NotificationFilter: content_availability_date: %s and access_duration: %s",
                        content_availability_date, access_duration
                        )
            if expiration_date and timezone.now() > expiration_date:
                logger.info("User %s has expired audit access to course %s", enrollment.user_id, course.id)
                user_ids.remove(enrollment.user_id)
        return user_ids

    def apply_filters(self, user_ids, course_key, notification_type) -> list:
        """
        Apply all the filters
        """
        notification_config = COURSE_NOTIFICATION_TYPES.get(notification_type, {})
        applicable_filters = notification_config.get('filters', [])
        course = modulestore().get_course(course_key)
        for filter_name in applicable_filters:
            logger.info(
                "NotificationFilter: Applying filter %s for notification type %s",
                filter_name,
                notification_type,
            )
            user_ids = getattr(self, filter_name)(user_ids, course)
        return user_ids
