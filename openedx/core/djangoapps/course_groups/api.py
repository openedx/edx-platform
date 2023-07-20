"""
course_groups API
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404

from common.djangoapps.student.models import get_user_by_username_or_email
from openedx.core.djangoapps.course_groups.models import CohortMembership, CourseUserGroup, CourseGroupsSettings, GroupMembership
from openedx.core.lib.courses import get_course_by_id

from .models import CourseUserGroupPartitionGroup, CourseGroup


def remove_user_from_cohort(course_key, username, cohort_id=None):
    """
    Removes an user from a course group.
    """
    if username is None:
        raise ValueError('Need a valid username')
    user = User.objects.get(username=username)
    if cohort_id is not None:
        membership = CohortMembership.objects.get(
            user=user, course_id=course_key, course_user_group__id=cohort_id
        )
        membership.delete()
    else:
        try:
            membership = CohortMembership.objects.get(user=user, course_id=course_key)
        except CohortMembership.DoesNotExist:
            pass
        else:
            membership.delete()

def get_assignment_type(user_group):
    """
    Get assignment type for cohort.
    """
    course_cohort = user_group.cohort
    return course_cohort.assignment_type


def _get_course_group_settings(course_key):
    return CourseGroupsSettings.objects.get(course_id=course_key)


def is_course_grouped(course_key):
    return _get_course_group_settings(course_key).is_cohorted


def get_group(user, course_key, assign=True, use_cached=False):
    if user is None or user.is_anonymous:
        return None

    if not is_course_grouped(course_key):
        return None

    try:
        membership = GroupMembership.objects.get(
            course_id=course_key,
            user_id=user.id,
        )
        return membership.course_user_group
    except GroupMembership.DoesNotExist:
        if not assign:
            return None

def get_group_by_id(course_key, group_id):
    """
    Return the CourseUserGroup object for the given cohort.  Raises DoesNotExist
    it isn't present.  Uses the course_key for extra validation.
    """
    return CourseUserGroup.objects.get(
        course_id=course_key,
        group_type=CourseUserGroup.GROUPS,
        id=group_id
    )


def link_group_to_partition_group(group, partition_id, group_id):
    """
    Create group to partition_id/group_id link.
    """
    CourseUserGroupPartitionGroup(
        course_user_group=group,
        partition_id=partition_id,
        group_id=group_id,
    ).save()


def unlink_group_partition_group(group):
    """
    Remove any existing group to partition_id/group_id link.
    """
    CourseUserGroupPartitionGroup.objects.filter(course_user_group=group).delete()


def get_course_group(course_id=None):
    query_set = CourseUserGroup.objects.filter(
        course_id=course_id,
        group_type=CourseUserGroup.GROUPS,
    )
    return list(query_set)


def is_group_exists(course_key, name):
    """
    Check if a group already exists.
    """
    return CourseUserGroup.objects.filter(course_id=course_key, group_type=CourseUserGroup.GROUPS, name=name).exists()


def add_group_to_course(name, course_key, professor=None):
    """
    Adds a group to a course.
    """
    if is_group_exists(course_key, name):
        raise ValueError("You cannot create two groups with the same name")

    try:
        course = get_course_by_id(course_key)
    except Http404:
        raise ValueError("Invalid course_key")  # lint-amnesty, pylint: disable=raise-missing-from

    return CourseGroup.create(
        group_name=name,
        course_id=course.id,
        professor=professor,
    ).course_user_group


def add_user_to_group(group, username_or_email_or_user):
    try:
        if hasattr(username_or_email_or_user, 'email'):
            user = username_or_email_or_user
        else:
            user = get_user_by_username_or_email(username_or_email_or_user)

        membership, previous_cohort = group.assign(group, user)
        return user, getattr(previous_cohort, 'name', None), False
    except User.DoesNotExist as ex:  # Note to self: TOO COHORT SPECIFIC!
        # If username_or_email is an email address, store in database.
        try:
            return (None, None, True)
        except ValidationError as invalid:
            if "@" in username_or_email_or_user:  # lint-amnesty, pylint: disable=no-else-raise
                raise invalid
            else:
                raise ex  # lint-amnesty, pylint: disable=raise-missing-from


def get_group_info_for_group(group):
    """
    Get the ids of the group and partition to which this cohort has been linked
    as a tuple of (int, int).

    If the cohort has not been linked to any group/partition, both values in the
    tuple will be None.

    The partition group info is cached for the duration of a request. Pass
    use_cached=True to use the cached value instead of fetching from the
    database.
    """
    try:
        return CourseUserGroupPartitionGroup.objects.get(course_user_group=group)
    except CourseUserGroupPartitionGroup.DoesNotExist:
        pass
