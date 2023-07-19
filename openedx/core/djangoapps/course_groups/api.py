"""
course_groups API
"""
from django.contrib.auth.models import User  # lint-amnesty, pylint: disable=imported-auth-user
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404

from openedx_filters.exceptions import OpenEdxFilterException
from openedx_filters.tooling import OpenEdxPublicFilter

from common.djangoapps.student.models import get_user_by_username_or_email
from openedx.core.djangoapps.course_groups.models import CohortMembership, CourseUserGroup
from openedx.core.lib.courses import get_course_by_id


class GroupMembershipException(Exception):
    pass


class GroupAssignmentNotAllowed(GroupMembershipException):
    pass



class GroupAssignmentRequested(OpenEdxPublicFilter):

    filter_type = "org.openedx.learning.group.assignment.requested.v1"

    class GroupAssignmentNotAllowed(OpenEdxFilterException):
        pass

    @classmethod
    def run_filter(cls, user, target_group):
        data = super().run_pipeline(user=user, target_group=target_group)
        return data.get("user"), data.get("target_group")


class GroupAdditionRequested(OpenEdxPublicFilter):

    filter_type = "org.openedx.learning.group.addition.requested.v1"

    class GroupAdditionNotAllowed(OpenEdxFilterException):
        pass

    @classmethod
    def run_filter(cls, group_class, name, course_key):
        data = super().run_pipeline(group_class=group_class, name=name, course_key=course_key)
        return data.get("group_class"), data.get("name"), data.get("course_key")


class GroupExistenceRequested(OpenEdxPublicFilter):

    filter_type = "org.openedx.learning.group.existence.requested.v1"

    @classmethod
    def run_filter(cls, group_class, name, course_key):
        data = super().run_pipeline(group_class=group_class, name=name, course_key=course_key)
        return data.get("group_class"), data.get("name"), data.get("course_key")


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


def is_group_exists(course_key, group_class, name):
    """
    Check if a group already exists.
    """
    # .. filter_implemented_name: GroupExistenceRequested
    # .. filter_type: org.openedx.learning.group.existence.requested.v1
    group_class, name, course_key = GroupExistenceRequested.run_filter(
        group_class=group_class,
        name=name,
        course_key=course_key,
    )
    return CourseUserGroup.objects.filter(course_id=course_key, group_type=group_class.type, name=name).exists()


def add_group_to_course(group_class, name, course_key):
    """
    Adds a group to a course.
    """
    try:
        # .. filter_implemented_name: GroupAdditionRequested
        # .. filter_type: org.openedx.learning.group.assignment.requested.v1
        group_class, name, course_key = GroupAdditionRequested.run_filter(
            group_class=group_class,
            name=name,
            course_key=course_key,
        )
    except GroupAdditionRequested.GroupAdditionNotAllowed as exc:
        raise GroupAssignmentNotAllowed(str(exc)) from exc

    if is_group_exists(course_key, name):
        raise ValueError(_("You cannot create two cohorts with the same name"))

    try:
        course = get_course_by_id(course_key)
    except Http404:
        raise ValueError("Invalid course_key")  # lint-amnesty, pylint: disable=raise-missing-from

    group = group_class.create(
        cohort_name=name,
        course_id=course.id,
        assignment_type=group_class.type
    ).course_user_group

    return group


def add_user_to_group(group, username_or_email_or_user):
    try:
        if hasattr(username_or_email_or_user, 'email'):
            user = username_or_email_or_user
        else:
            user = get_user_by_username_or_email(username_or_email_or_user)

        try:
            # .. filter_implemented_name: GroupAssignmentRequested
            # .. filter_type: org.openedx.learning.group.assignment.requested.v1
            user, group = GroupAssignmentRequested.run_filter(user=user, target_group=group)
        except GroupAssignmentRequested.PreventGroupAssignment as exc:
            raise GroupAssignmentNotAllowed(str(exc)) from exc

        membership, previous_cohort = group.assign(group, user)
        return user, getattr(previous_cohort, 'name', None), False
    except User.DoesNotExist as ex:  # Note to self: TOO COHORT SPECIFIC!
        # If username_or_email is an email address, store in database.
        try:
            validate_email(username_or_email_or_user)
            try:
                assignment = UnregisteredLearnerCohortAssignments.objects.get(
                    email=username_or_email_or_user, course_id=cohort.course_id
                )
                assignment.course_user_group = cohort
                assignment.save()
            except UnregisteredLearnerCohortAssignments.DoesNotExist:
                assignment = UnregisteredLearnerCohortAssignments.objects.create(
                    course_user_group=cohort, email=username_or_email_or_user, course_id=cohort.course_id
                )
            return (None, None, True)
        except ValidationError as invalid:
            if "@" in username_or_email_or_user:  # lint-amnesty, pylint: disable=no-else-raise
                raise invalid
            else:
                raise ex  # lint-amnesty, pylint: disable=raise-missing-from
