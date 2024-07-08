"""
Audience based filters for notifications
"""

from abc import abstractmethod

from opaque_keys.edx.keys import CourseKey

from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseStaffRole, CourseInstructorRole
from lms.djangoapps.discussion.django_comment_client.utils import get_users_with_roles
from lms.djangoapps.teams.models import CourseTeam
from openedx.core.djangoapps.course_groups.models import CourseUserGroup
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


class ForumRoleAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for roles
    """
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


class CourseRoleAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for course roles
    """
    allowed_filters = ['staff', 'instructor']

    def filter(self, course_roles):
        """
        Filter users based on their course roles
        """
        if not self.is_valid_filter(course_roles):
            raise ValueError(f'Invalid roles {course_roles} passed to CourseRoleAudienceFilter')

        user_ids = []

        course_key = self.course_key
        if not isinstance(course_key, CourseKey):
            course_key = CourseKey.from_string(course_key)

        if 'staff' in course_roles:
            staff_users = CourseStaffRole(course_key).users_with_role().values_list('id', flat=True)
            user_ids.extend(staff_users)

        if 'instructor' in course_roles:
            instructor_users = CourseInstructorRole(course_key).users_with_role().values_list('id', flat=True)
            user_ids.extend(instructor_users)

        return user_ids


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
            is_active=True,
        ).values_list('user_id', flat=True)


class TeamAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for team roles
    """

    def filter(self, team_ids):
        """
        Filter users based on team id
        """
        teams = CourseTeam.objects.filter(team_id__in=team_ids, course_id=self.course_key)

        if not teams:   # invalid team ids passed
            raise ValueError(f'Invalid Team ids {team_ids} passed to TeamAudienceFilter for course {self.course_key}')

        user_ids = []
        for team in teams:
            user_ids.extend(team.users.all().values_list('id', flat=True))

        return user_ids


class CohortAudienceFilter(NotificationAudienceFilterBase):
    """
    Filter class for cohort roles
    """

    def filter(self, group_ids):
        """
        Filter users based on their cohort ids
        """
        users_in_cohort = CourseUserGroup.objects.filter(
            course_id=self.course_key, id__in=group_ids
        ).values_list('users__id', flat=True)
        return users_in_cohort
