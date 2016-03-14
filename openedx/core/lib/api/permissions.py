"""
API library for Django REST Framework permissions-oriented workflows
"""

from django.conf import settings
from django.http import Http404
from rest_framework import permissions

from student.roles import CourseStaffRole


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
        return (
            (settings.DEBUG and api_key is None) or
            (api_key is not None and request.META.get("HTTP_X_EDX_API_KEY") == api_key)
        )


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
            or (user.username == getattr(request, 'data', {}).get('username'))
