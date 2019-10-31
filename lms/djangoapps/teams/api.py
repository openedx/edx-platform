"""
The Python API other app should use to work with Teams feature
"""
from __future__ import absolute_import, unicode_literals

import logging
from enum import Enum

from django.db.models import Count

from course_modes.models import CourseMode
from lms.djangoapps.discussion.django_comment_client.utils import has_discussion_privileges
from lms.djangoapps.teams.models import CourseTeam
from student.models import CourseEnrollment
from student.roles import CourseInstructorRole, CourseStaffRole

logger = logging.getLogger(__name__)


class OrganizationProtectionStatus(Enum):
    """
    Enum for the different protection status a user can be in related to their
    course enrollment mode.

    "protection_exempt" means the user is a course or org staff that do not need to be protected.

    "protected" means the learner is part of an organization and should be in an exclusive team

    "unprotected" means the learner is part of the general edX learner in audit or verified tracks
    """
    protected = 'org_protected'
    protection_exempt = 'org_protection_exempt'
    unprotected = 'org_unprotected'


ORGANIZATION_PROTECTED_MODES = (
    CourseMode.MASTERS,
)


def get_team_by_discussion(discussion_id):
    """
    This is a function to get team object by the discussion_id passed in.
    If the discussion_id is not associated with any team, we return None
    """
    try:
        return CourseTeam.objects.get(discussion_topic_id=discussion_id)
    except CourseTeam.DoesNotExist:
        # When the discussion does not belong to a team. It's visible in
        # any team context
        return None


def is_team_discussion_private(team):
    """
    This is the function to check if the team is configured to have its discussion
    to be private. We need a way to check the setting on the team.
    This function also provide ways to toggle the setting of discussion visibility on the
    individual team level.
    To be followed up by MST-25
    """
    return getattr(team, 'is_discussion_private', False)


def user_is_a_team_member(user, team):
    """
    Return if the user is a member of the team
    If the team is not defined, return False
    """
    if team:
        return team.users.filter(id=user.id).exists()
    return False


def discussion_visible_by_user(discussion_id, user):
    """
    This function checks whether the discussion should be visible to the user.
    The discussion should not be visible to the user if
    * The discussion is part of the Team AND
    * The team is configured to hide the discussions from non-teammembers AND
    * The user is not part of the team
    """
    team = get_team_by_discussion(discussion_id)
    return not is_team_discussion_private(team) or user_is_a_team_member(user, team)


def _has_course_staff_privileges(user, course_key):
    """
    Returns True if the user is an admin for the course, else returns False
    """
    if user.is_staff:
        return True
    if CourseStaffRole(course_key).has_user(user) or CourseInstructorRole(course_key).has_user(user):
        return True
    return False


def has_team_api_access(user, course_key, access_username=None):
    """Returns True if the user has access to the Team API for the course
    given by `course_key`. The user must either be enrolled in the course,
    be course staff, be global staff, or have discussion privileges.

    Args:
      user (User): The user to check access for.
      course_key (CourseKey): The key to the course which we are checking access to.
      access_username (string): If provided, access_username must match user.username for non staff access.

    Returns:
      bool: True if the user has access, False otherwise.
    """
    if _has_course_staff_privileges(user, course_key):
        return True
    if has_discussion_privileges(user, course_key):
        return True
    if not access_username or access_username == user.username:
        return CourseEnrollment.is_enrolled(user, course_key)
    return False


def user_organization_protection_status(user, course_key):
    """
    Returns the organization protection status of the user related to this course
    If the user is in the Masters track of the course, we return the protected status.
    If the user is a staff of the course, we return the protection_exempt status
    else, we return the unprotected status
    """
    if _has_course_staff_privileges(user, course_key):
        return OrganizationProtectionStatus.protection_exempt
    enrollment = CourseEnrollment.get_enrollment(user, course_key)
    if enrollment and enrollment.is_active:
        if enrollment.mode in ORGANIZATION_PROTECTED_MODES:
            return OrganizationProtectionStatus.protected
        else:
            return OrganizationProtectionStatus.unprotected
    else:
        raise ValueError(
            'Cannot check the org_protection status on a student [%s] not enrolled in course [%s]',
            user.id,
            course_key
        )


def has_specific_team_access(user, team):
    """
    Check whether the user have access to the specific team.
    The user can be of a different organization protection bubble with the team in question.
    If user is not in the same organization protection bubble with the team, return False.
    Else, return True. If the user is a course admin, also return true
    """
    protection_status = user_organization_protection_status(user, team.course_id)
    if protection_status == OrganizationProtectionStatus.protection_exempt:
        return True
    if team.organization_protected:
        return OrganizationProtectionStatus.protected == protection_status
    else:
        return OrganizationProtectionStatus.unprotected == protection_status


def get_team_count_query_set(topic_id_set, course_id, organization_protection_status):
    """ Helper function to get the team count query set based on the filters provided """

    filter_query = {'course_id': course_id}
    if len(topic_id_set) == 1:
        filter_query.update({'topic_id': topic_id_set[0]})
    else:
        filter_query.update({'topic_id__in': topic_id_set})

    if organization_protection_status != OrganizationProtectionStatus.protection_exempt:
        filter_query.update(
            {'organization_protected': organization_protection_status == OrganizationProtectionStatus.protected}
        )
    return CourseTeam.objects.filter(**filter_query)


def add_team_count(topics, course_id, organization_protection_status):
    """
    Helper method to add team_count for a list of topics.
    This allows for a more efficient single query.
    """
    topic_ids = [topic['id'] for topic in topics]
    teams_query_set = get_team_count_query_set(
        topic_ids,
        course_id,
        organization_protection_status
    )

    teams_per_topic = teams_query_set.values('topic_id').annotate(team_count=Count('topic_id'))

    topics_to_team_count = {d['topic_id']: d['team_count'] for d in teams_per_topic}
    for topic in topics:
        topic['team_count'] = topics_to_team_count.get(topic['id'], 0)
