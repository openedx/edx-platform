"""
API library for Django REST Framework permissions-oriented workflows
"""
from rest_framework.permissions import BasePermission

from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.roles import CourseInstructorRole, CourseStaffRole, GlobalStaff
from openedx.core.djangoapps.course_roles.helpers import user_has_permission_course, user_has_permission_list_any_course
from openedx.core.djangoapps.course_roles.permissions import CourseRolesPermission
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
        # TODO: course roles: If the course roles feature flag is disabled the user_has_permission_course
        # below will never return true. Remove the CourseInstructorRole and
        # CourseStaffRole checks when course_roles Django app are implemented.
        return (
            CourseInstructorRole(course_key).has_user(request.user) or
            CourseStaffRole(course_key).has_user(request.user) or
            user_has_permission_course(request.user, CourseRolesPermission.MANAGE_CONTENT.value, course_key)
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

        permissions = [
            CourseRolesPermission.VIEW_ALL_CONTENT.value,
            CourseRolesPermission.VIEW_ONLY_LIVE_PUBLISHED_CONTENT.value,
            CourseRolesPermission.VIEW_ALL_PUBLISHED_CONTENT.value
        ]
        # TODO: course roles: If the course roles feature flag is disabled the user_has_permission_list_course
        # below will never return true. Remove the CourseInstructorRole and
        # CourseStaffRole checks when course_roles Django app are implemented.
        return (
            CourseInstructorRole(course_key).has_user(request.user) or
            CourseStaffRole(course_key).has_user(request.user) or
            user_has_permission_list_any_course(request.user, permissions, course_key) or
            CourseEnrollment.is_enrolled(request.user, course_key)
        )
