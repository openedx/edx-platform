"""
API library for Django REST Framework permissions-oriented workflows
"""

from django.conf import settings
from django.http import Http404
from rest_framework import permissions

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from student.roles import CourseStaffRole, CourseInstructorRole

from openedx.core.lib.log_utils import audit_log


class ApiKeyHeaderPermission(permissions.BasePermission):
    """
    Django REST Framework permissions class used to manage API Key integrations
    """

    def has_permission(self, request, view):
        """
        Check for permissions by matching the configured API key and header

        If settings.DEBUG is True and settings.EDX_API_KEY is not set or None,
        then allow the request. Otherwise, allow the request if and only if
        settings.EDX_API_KEY is set and the X-Edx-Api-Key HTTP header is
        present in the request and matches the setting.
        """
        api_key = getattr(settings, "EDX_API_KEY", None)

        if settings.DEBUG and api_key is None:
            return True

        elif api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key:
            audit_log("ApiKeyHeaderPermission used",
                      path=request.path,
                      ip=request.META.get("REMOTE_ADDR"))
            return True

        return False


class ApiKeyHeaderPermissionIsAuthenticated(ApiKeyHeaderPermission, permissions.IsAuthenticated):
    """
    Allow someone to access the view if they have the API key OR they are authenticated.

    See ApiKeyHeaderPermission for more information how the API key portion is implemented.
    """

    def has_permission(self, request, view):
        # TODO We can optimize this later on when we know which of these methods is used more often.
        api_permissions = ApiKeyHeaderPermission.has_permission(self, request, view)
        is_authenticated_permissions = permissions.IsAuthenticated.has_permission(self, request, view)
        return api_permissions or is_authenticated_permissions


class IsUserInUrl(permissions.BasePermission):
    """
    Permission that checks to see if the request user matches the user in the URL.
    """

    def has_permission(self, request, view):
        """
        Returns true if the current request is by the user themselves.

        Note: a 404 is returned for non-staff instead of a 403. This is to prevent
        users from being able to detect the existence of accounts.
        """
        url_username = request.parser_context.get('kwargs', {}).get('username', '')
        if request.user.username.lower() != url_username.lower():
            if request.user.is_staff:
                return False  # staff gets 403
            raise Http404()
        return True


class IsCourseStaffInstructor(permissions.BasePermission):
    """
    Permission to check that user is a course instructor or staff of
    a master course given a course object or the user is a coach of
    the course itself.
    """

    def has_object_permission(self, request, view, obj):
        return (hasattr(request, 'user') and
                # either the user is a staff or instructor of the master course
                (hasattr(obj, 'course_id') and
                 (CourseInstructorRole(obj.course_id).has_user(request.user) or
                  CourseStaffRole(obj.course_id).has_user(request.user))) or
                # or it is a safe method and the user is a coach on the course object
                (request.method in permissions.SAFE_METHODS
                 and hasattr(obj, 'coach') and obj.coach == request.user))


class IsMasterCourseStaffInstructor(permissions.BasePermission):
    """
    Permission to check that user is instructor or staff of the master course.
    """
    def has_permission(self, request, view):
        """
        This method is assuming that a `master_course_id` parameter
        is available in the request as a GET parameter, a POST parameter
        or it is in the JSON payload included in the request.
        The reason is because this permission class is going
        to check if the user making the request is an instructor
        for the specified course.
        """
        master_course_id = (request.GET.get('master_course_id')
                            or request.POST.get('master_course_id')
                            or request.data.get('master_course_id'))
        if master_course_id is not None:
            try:
                course_key = CourseKey.from_string(master_course_id)
            except InvalidKeyError:
                raise Http404()
            return (hasattr(request, 'user') and
                    (CourseInstructorRole(course_key).has_user(request.user) or
                     CourseStaffRole(course_key).has_user(request.user)))
        return False


class IsUserInUrlOrStaff(IsUserInUrl):
    """
    Permission that checks to see if the request user matches the user in the URL or has is_staff access.
    """

    def has_permission(self, request, view):
        if request.user.is_staff:
            return True

        return super(IsUserInUrlOrStaff, self).has_permission(request, view)


class IsStaffOrReadOnly(permissions.BasePermission):
    """Permission that checks to see if the user is global or course
    staff, permitting only read-only access if they are not.
    """

    def has_object_permission(self, request, view, obj):
        return (request.user.is_staff or
                CourseStaffRole(obj.course_id).has_user(request.user) or
                request.method in permissions.SAFE_METHODS)


class IsStaffOrOwner(permissions.BasePermission):
    """
    Permission that allows access to admin users or the owner of an object.
    The owner is considered the User object represented by obj.user.
    """

    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or obj.user == request.user

    def has_permission(self, request, view):
        user = request.user
        return user.is_staff \
            or (user.username == request.GET.get('username')) \
            or (user.username == getattr(request, 'data', {}).get('username')) \
            or (user.username == getattr(view, 'kwargs', {}).get('username'))
