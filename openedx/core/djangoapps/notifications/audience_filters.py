"""
Audience based filters for notifications
"""

from abc import abstractmethod

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from lms.djangoapps.discussion.django_comment_client.utils import get_users_with_roles
from openedx.core.djangoapps.django_comment_common.models import (
    FORUM_ROLE_ADMINISTRATOR,
    FORUM_ROLE_MODERATOR,
    FORUM_ROLE_GROUP_MODERATOR,
    FORUM_ROLE_COMMUNITY_TA,
    FORUM_ROLE_STUDENT,
)


class NotificationAudienceFilterBase:
    """
    Base class for notification audience filters
    """
    def __init__(self, course_key):
        self.course_key = course_key

    allowed_filters = []

    def is_valid_filter(self, values):
        return all(value in self.allowed_filters for value in values)

    @abstractmethod
    def filter(self, values):
        pass


class RoleAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for roles
    """
    # TODO: Add course roles to this. We currently support only forum roles
    allowed_filters = [
        FORUM_ROLE_ADMINISTRATOR,
        FORUM_ROLE_MODERATOR,
        FORUM_ROLE_GROUP_MODERATOR,
        FORUM_ROLE_COMMUNITY_TA,
        FORUM_ROLE_STUDENT,
    ]

    def filter(self, roles):
        """
        Filter users based on their roles
        """
        if not self.is_valid_filter(roles):
            raise ValueError(f'Invalid roles {roles} passed to RoleAudienceFilter')
        return [user.id for user in get_users_with_roles(roles, self.course_key)]


class EnrollmentAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for enrollment modes
    """
    allowed_filters = CourseMode.ALL_MODES

    def filter(self, enrollment_modes):
        """
        Filter users based on their course enrollment modes
        """
        if not self.is_valid_filter(enrollment_modes):
            raise ValueError(f'Invalid enrollment modes {enrollment_modes} passed to EnrollmentAudienceFilter')
        return CourseEnrollment.objects.filter(
            course_id=self.course_key,
            mode__in=enrollment_modes,
        ).values_list('user_id', flat=True)
