"""
Helpers for the course roles app.
"""
from typing import Union, List

from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.utils.translation import gettext as _
from opaque_keys.edx.keys import CourseKey

from edx_toggles.toggles import WaffleFlag
from openedx.core.djangoapps.course_roles.models import UserRole
from openedx.core.djangoapps.course_roles.permissions import CourseRolesPermission
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


def user_has_permission_course(
        user: Union[User, AnonymousUser],
        permission: Union[CourseRolesPermission, str],
        course_key: CourseKey
):
    """
    Check if a user has a permission in a course.
    """
    if not use_permission_checks():
        return False
    elif isinstance(user, AnonymousUser):
        return False
    if isinstance(permission, CourseRolesPermission):
        permission = permission.value.name
    return UserRole.objects.filter(
        user=user,
        role__permissions__name=permission,
        course=course_key,
    ).exists()


def user_has_permission_list_course(
        user: Union[User, AnonymousUser],
        permissions: List[Union[CourseRolesPermission, str]],
        course_key: CourseKey
):
    """
    Check if a user has all of the given permissions in a course.
    """
    if not use_permission_checks():
        return False
    return all(user_has_permission_course(user, permission, course_key) for permission in permissions)


def user_has_permission_list_any_course(
        user: Union[User, AnonymousUser],
        permissions: List[Union[CourseRolesPermission, str]],
        course_key: CourseKey
):
    """
    Check if a user has ANY of the given permissions in a course.
    """
    return any(user_has_permission_course(user, permission, course_key) for permission in permissions)


def user_has_permission_org(
        user: Union[User, AnonymousUser],
        permission: Union[CourseRolesPermission, str],
        organization_name: str
):
    """
    Check if a user has a permission for all courses in an organization.
    """
    if not use_permission_checks():
        return False
    elif isinstance(user, AnonymousUser):
        return False
    if isinstance(permission, CourseRolesPermission):
        permission = permission.value.name
    return UserRole.objects.filter(
        user=user,
        role__permissions__name=permission,
        course__isnull=True,
        org__name=organization_name,
    ).exists()


def user_has_permission_list_org(
        user: Union[User, AnonymousUser],
        permissions: List[Union[CourseRolesPermission, str]],
        organization_name: str
):
    """
    Check if a user has ALL of the given permissions for all courses in an organization.
    """
    if not use_permission_checks():
        return False
    return all(
        user_has_permission_org(user, permission, organization_name) for permission in permissions
    )


def user_has_permission_course_org(
        user: Union[User, AnonymousUser],
        permission: Union[CourseRolesPermission, str],
        course_key: CourseKey,
        organization_name: str = None
):
    """
    Check if a user has a permission for all courses in an organization or for a specific course.
    """
    if not use_permission_checks():
        return False
    elif isinstance(user, AnonymousUser):
        return False
    if isinstance(permission, CourseRolesPermission):
        permission = permission.value.name
    if organization_name is None:
        organization_name = course_key.org
    return (user_has_permission_course(user, permission, course_key) or
            user_has_permission_org(user, permission, organization_name)
            )


def user_has_permission_list_course_org(
        user: Union[User, AnonymousUser],
        permissions: List[Union[CourseRolesPermission, str]],
        course_key: CourseKey,
        organization_name: str = None
):
    """
    Check if a user has all of the given permissions for all courses in an organization or for a specific course.
    """
    if not use_permission_checks():
        return False
    return all(
        user_has_permission_course_org(user, permission, course_key, organization_name)
        for permission in permissions
    )


def get_all_user_permissions_for_a_course(user_id: int, course_key: CourseKey):
    """
    Get all of a user's permissions for a course,
    including, if applicable, organization-wide permissions
    and instance-wide permissions.
    """
    if user_id is None:
        raise ValueError('user_id must not be None')
    if course_key is None:
        raise ValueError('course_key must not be None')
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist as exc:
        raise ValueError(_('user does not exist')) from exc
    try:
        course = modulestore().get_course(course_key)
    except AssertionError as exc:
        raise ValueError(_('course_id is not valid')) from exc
    if not course:
        raise ValueError(_('course does not exist'))
    course_permissions = set(UserRole.objects.filter(
        user__id=user_id,
        course=course_key,
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
