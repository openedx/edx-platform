"""
Helpers for the course roles app.
"""
from __future__ import annotations

from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey
from opaque_keys.edx.locator import LibraryLocator

from edx_django_utils.cache import RequestCache
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.models import UserRole
from openedx.core.djangoapps.course_roles.toggles import use_permission_checks
from openedx.core.lib.exceptions import CourseNotFoundError


def get_all_user_permissions_for_a_course(
    user: User | AnonymousUser, course_key: CourseKey
) -> set[CourseRolesPermission]:
    """
    Get all of a user's permissions for a course,
    including, if applicable, organization-wide permissions
    and instance-wide permissions.
    """
    if isinstance(user, AnonymousUser):
        return set()
    if not isinstance(course_key, CourseKey):
        raise TypeError(f'course_key must be a CourseKey, not {type(course_key)}')
    if isinstance(course_key, LibraryLocator):
        return set()
    if not isinstance(user, User):
        raise TypeError(f'user must be a User, not {type(user)}')
    cache = RequestCache("course_roles")
    cache_key = f"all_user_permissions_for_course:{user.id}:{course_key}"
    cached_response = cache.get_cached_response(cache_key)
    if cached_response.is_found:
        return cached_response.value
    if not CourseOverview.course_exists(course_key):
        raise CourseNotFoundError(f'course does not exist: {course_key}')
    permissions_qset = UserRole.objects.filter(
        Q(user=user),
        (
            # Course-specific roles
            Q(course=course_key) |
            # Org-wide roles that apply to this course
            (Q(course__isnull=True) & Q(org__name=course_key.org)) |
            # Instance-wide roles
            (Q(course__isnull=True) & Q(org__isnull=True))
        )
    )
    permissions = set(
        CourseRolesPermission[permission_name.upper()]
        for permission_name
        in permissions_qset.values_list('role__permissions__name', flat=True)
    )
    cache.set(cache_key, permissions)

    return permissions


def get_all_courses_for_user_has_permission(user: User, permission: CourseRolesPermission) -> set[CourseKey]:
    """
    Get all courses for a user with permission.
    """
    if not use_permission_checks():
        return set()
    if isinstance(user, AnonymousUser):
        return set()
    if not isinstance(user, User):
        raise TypeError(f'user must be a User, not {type(user)}')
    if not isinstance(permission, CourseRolesPermission):
        raise TypeError(f'permission must be a CourseRolesPermission, not {type(permission)}')
    cache = RequestCache("course_roles")
    cache_key = f"all_courses_for_user_with_permission:{user.id}:{permission.value.name}"
    cached_response = cache.get_cached_response(cache_key)
    if cached_response.is_found:
        return cached_response.value
    courses_qset = UserRole.objects.filter(
        Q(user=user) &
        Q(role__permissions__name=permission.value.name) &
        Q(course__isnull=False)
    )
    courses = set(CourseKey.from_string(str(course)) for course in courses_qset.values_list('course__id', flat=True))
    orgs_qset = UserRole.objects.filter(
        Q(user=user) &
        Q(role__permissions__name=permission.value.name) &
        Q(course__isnull=True)
    )
    orgs = set(org for org in orgs_qset.values_list('org__name', flat=True))
    if orgs:
        courses_qset = CourseOverview.objects.filter(
            Q(org__in=orgs)
        )
        courses |= set(CourseKey.from_string(str(course)) for course in courses_qset.values_list('id', flat=True))
    cache.set(cache_key, courses)
    return courses
