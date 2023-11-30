"""
Helpers for the course roles app.
"""
from __future__ import annotations

from django.contrib.auth.models import AnonymousUser, User  # lint-amnesty, pylint: disable=imported-auth-user
from django.db.models import Q
from opaque_keys.edx.keys import CourseKey

from edx_django_utils.cache import RequestCache
from edx_toggles.toggles import WaffleFlag
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_roles.models import UserRole
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission


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
        raise TypeError('course_key must be a CourseKey')
    if not isinstance(user, User):
        raise TypeError('user must be a User')
    cache = RequestCache("course_roles")
    cache_key = f"all_user_permissions_for_course:{user.id}:{course_key}"
    cached_response = cache.get_cached_response(cache_key)
    if cached_response.is_found:
        return cached_response.value
    if not CourseOverview.course_exists(course_key):
        raise ValueError('course does not exist')
    permissions_qset = UserRole.objects.filter(
        Q(user=user),
        (
            # Course-specific roles
            Q(course=course_key) |
            # Org-wide roles that apply to this course
            (Q(course__isnull=True) & Q(org__name=course_key.org)) |
            # Instance-wide roles
            Q(org__isnull=True)
        )
    )
    permissions = set(
        CourseRolesPermission[permission_name.upper()]
        for permission_name
        in permissions_qset.values_list('role__permissions__name', flat=True)
    )
    cache.set(cache_key, permissions)

    return permissions
