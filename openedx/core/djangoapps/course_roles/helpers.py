"""
Helpers for the course roles djangoapp which is used for authorization.
"""
from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.utils.translation import gettext as _

from edx_toggles.toggles import WaffleFlag
from openedx.core.djangoapps.course_roles.models import UserRole
from xmodule.modulestore.django import modulestore


# .. toggle_name: FLAG_USE_PERMISSION_CHECKS
# .. toggle_implementation: WaffleFlag
# .. toggle_default: False
# .. toggle_description: Enabling the toggle will allow the db checks for a users permissions. These are used alongside current
#   roles checks. If the flag is not enabled, only the roles checks will be used.
# .. toggle_use_cases: temporary
# .. toggle_creation_date: 2023-10-17
# .. toggle_target_removal_date: 2023-12-01
# .. toggle_warning:
USE_PERMISSION_CHECKS_FLAG = WaffleFlag('course_roles.use_permission_checks', module_name=__name__) or False  # lint-amnesty, pylint: disable=toggle-missing-annotation


def use_permission_checks():
    """
    Returns ture if permissions checks should be used
    """
    return USE_PERMISSION_CHECKS_FLAG.is_enabled()


def user_has_permission_course(user, permission_name, course_id):
    """
    Check if a user has a permission in a course.
    """
    if not use_permission_checks():
        return False
    if isinstance(user, AnonymousUser) or not isinstance(user, User):
        return False
    return UserRole.objects.filter(
        user=user,
        role__permissions__name=permission_name,
        course=course_id,
    ).exists()


def user_has_permission_list_course(user, permission_names, course_id):
    """
    Check if a user has ALL of the given permissions in a course.
    """
    if not use_permission_checks():
        return False
    return all(user_has_permission_course(user, permission_name, course_id) for permission_name in permission_names)


def user_has_permission_list_any_course(user, permission_names, course_id):
    """
    Check if a user has ANY of the given permissions in a course.
    """
    return any(user_has_permission_course(user, permission_name, course_id) for permission_name in permission_names)


def user_has_permission_org(user, permission_name, organization_name):
    """
    Check if a user has a permission for all courses in an organization.
    """
    if not use_permission_checks():
        return False
    if isinstance(user, AnonymousUser) or not isinstance(user, User):
        return False
    return UserRole.objects.filter(
        user=user,
        role__permissions__name=permission_name,
        course__isnull=True,
        org__name=organization_name,
    ).exists()


def user_has_permission_list_org(user, permission_names, organization_name):
    """
    Check if a user has ALL of the given permissions for all courses in an organization.
    """
    if not use_permission_checks():
        return False
    return all(
        user_has_permission_org(user, permission_name, organization_name) for permission_name in permission_names
    )


def user_has_permission_course_org(user, permission_name, course_id, organization_name=None):
    """
    Check if a user has a permission for all courses in an organization or for a specific course.
    """
    if not use_permission_checks():
        return False
    if isinstance(user, AnonymousUser) or not isinstance(user, User):
        return False
    if organization_name is None:
        course = modulestore().get_course(course_id)
        if course:
            organization_name = course.org
        else:
            return user_has_permission_course(user, permission_name, course_id)
    return (user_has_permission_course(user, permission_name, course_id) or
            user_has_permission_org(user, permission_name, organization_name)
            )


def user_has_permission_list_course_org(user, permission_names, course_id, organization_name=None):
    """
    Check if a user has all of the given permissions for all courses in an organization or for a specific course.
    """
    if not use_permission_checks():
        return False
    return all(
        user_has_permission_course_org(user, permission_name, course_id, organization_name)
        for permission_name in permission_names
    )


def get_all_user_permissions_for_a_course(user_id, course_id):
    """
    Get all of a user's permissions for a course,
    including, if applicable, organization-wide permissions
    and instance-wide permissions.
    """
    if user_id is None or course_id is None:
        raise ValueError(_('user_id and course_id must not be None'))
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise ValueError(_('user does not exist')) from exc
    try:
        course = modulestore().get_course(course_id)
    except AssertionError as exc:
        raise ValueError(_('course_id is not valid')) from exc
    if not course:
        raise ValueError(_('course does not exist'))
    course_permissions = set(UserRole.objects.filter(
        user__id=user_id,
        course=course_id,
    ).values_list('role__permissions__name', flat=True))
    organization_name = course.org
    organization_permissions = set(UserRole.objects.filter(
        user__id=user_id,
        course__isnull=True,
        org__name=organization_name,
    ).values_list('role__permissions__name', flat=True))
    permissions = course_permissions.union(organization_permissions)
    instance_permissions = set(UserRole.objects.filter(
        user__id=user_id,
        course__isnull=True,
        org__isnull=True,
    ).values_list('role__permissions__name', flat=True))
    permissions = permissions.union(instance_permissions)
    return permissions
