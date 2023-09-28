"""
Helpers for the course roles app.
"""
from django.contrib.auth.models import AnonymousUser

from openedx.core.djangoapps.course_roles.models import CourseRolesUserRole
from openedx.core.lib.cache_utils import request_cached


@request_cached()
def course_permission_check(user, permission_name, course_id):
    """
    Check if a user has a permission in a course.
    """
    if isinstance(user, AnonymousUser):
        return False
    return CourseRolesUserRole.objects.filter(
        user=user,
        role__permissions__name=permission_name,
        course=course_id,
    ).exists()


@request_cached()
def course_permissions_list_check(user, permission_names, course_id):
    """
    Check if a user has all of the given permissions in a course.
    """
    return all(course_permission_check(user, permission_name, course_id) for permission_name in permission_names)


@request_cached()
def organization_permission_check(user, permission_name, organization_name):
    """
    Check if a user has a permission in an organization.
    """
    if isinstance(user, AnonymousUser):
        return False
    return CourseRolesUserRole.objects.filter(
        user=user,
        role__permissions__name=permission_name,
        course__isnull=True,
        org__name=organization_name,
    ).exists()


@request_cached()
def organization_permissions_list_check(user, permission_names, organization_name):
    """
    Check if a user has all of the given permissions in an organization.
    """
    return all(
        organization_permission_check(user, permission_name, organization_name) for permission_name in permission_names
    )
