"""
API library for Django REST Framework permissions-oriented workflows
"""
from rest_framework.permissions import BasePermission

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.lib.api.view_utils import validate_course_key


class IsStaffOrInstructor(BasePermission):
    """
    Check if user is global or course staff

    Permission that checks to see if the user is global staff, course
    staff, course admin,If none of those conditions are met, HTTP403 is returned.
    """

    def has_permission(self, request, view):
        course_key_string = view.kwargs.get('course_id')
        course_key = validate_course_key(course_key_string)

        if GlobalStaff().has_user(request.user):
            return True
        # TODO: remove role checks once course_roles is fully impelented and data is migrated
        return (
            CourseInstructorRole(course_key).has_user(request.user) or
            CourseStaffRole(course_key).has_user(request.user) or
            request.user.has_perm(f'course_roles.{CourseRolesPermission.MANAGE_CONTENT.value.name}')
        )


class IsEnrolledOrStaff(BasePermission):
    """
    Check if user is enrolled in the course or staff
    """

    def has_permission(self, request, view):
        course_key_string = view.kwargs.get('course_id')
        course_key = validate_course_key(course_key_string)

        if GlobalStaff().has_user(request.user):
            return True

        user_has_permissions = (
            request.user.has_perm(
                f'course_roles.{CourseRolesPermission.VIEW_ALL_CONTENT.value.name}'
            ) or
            request.user.has_perm(
                f'course_roles.{CourseRolesPermission.VIEW_LIVE_PUBLISHED_CONTENT.value.name}'
            ) or
            request.user.has_perm(
                f'course_roles.{CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.value.name}'
            )
        )
        # TODO: remove role checks once course_roles is fully impelented and data is migrated
        return (
            CourseInstructorRole(course_key).has_user(request.user) or
            CourseStaffRole(course_key).has_user(request.user) or
            CourseEnrollment.is_enrolled(request.user, course_key) or
            user_has_permissions
        )
