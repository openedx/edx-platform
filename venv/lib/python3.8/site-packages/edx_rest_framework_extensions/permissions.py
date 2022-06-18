""" Permission classes. """
import logging

from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import BasePermission, IsAuthenticated

from edx_rest_framework_extensions.auth.jwt.authentication import is_jwt_authenticated
from edx_rest_framework_extensions.auth.jwt.decoder import (
    decode_jwt_filters,
    decode_jwt_is_restricted,
    decode_jwt_scopes,
)


log = logging.getLogger(__name__)


class IsSuperuser(BasePermission):
    """ Allows access only to superusers. """

    def has_permission(self, request, view):
        return request.user and request.user.is_superuser


class IsStaff(BasePermission):
    """
    Allows access to "global" staff users..
    """
    def has_permission(self, request, view):
        return request.user.is_staff


class IsUserInUrl(BasePermission):
    """
    Allows access if the requesting user matches the user in the URL.
    """
    def has_permission(self, request, view):
        allowed = request.user.username.lower() == get_username_param(request)
        if not allowed:
            log.info("Permission IsUserInUrl: not satisfied for requesting user %s.", request.user.username)
        return allowed


class JwtRestrictedApplication(BasePermission):
    """
    Allows access if the request was successfully authenticated with JwtAuthentication
    by a RestrictedApplication.
    """
    message = 'Not a Restricted JWT Application.'

    def has_permission(self, request, view):
        ret_val = is_jwt_authenticated(request) and decode_jwt_is_restricted(request.auth)
        log.debug("Permission JwtRestrictedApplication: returns %s.", ret_val)
        return ret_val


class NotJwtRestrictedApplication(BasePermission):
    """
    Allows access if either the request was not authenticated with JwtAuthentication, or
    if it was successfully authenticated with JwtAuthentication and the Jwt was not
    flagged as restricted.

    Note: Anonymous access will also pass this permission.

    """
    def has_permission(self, request, view):
        return not JwtRestrictedApplication().has_permission(request, view)


class JwtHasScope(BasePermission):
    """
    The request is authenticated as a user and the token used has the right scope.
    """
    message = 'JWT missing required scopes.'

    def has_permission(self, request, view):
        jwt_scopes = decode_jwt_scopes(request.auth)
        required_scopes = set(getattr(view, 'required_scopes', []))
        allowed = bool(required_scopes) and required_scopes.issubset(jwt_scopes)
        if not allowed:
            log.warning(
                "Permission JwtHasScope: required scopes '%s' are not a subset of the token's scopes '%s'.",
                required_scopes,
                jwt_scopes,
            )
        return allowed


class JwtHasContentOrgFilterForRequestedCourse(BasePermission):
    """
    The JWT used to authenticate contains the appropriate content provider
    filter for the requested course resource.
    """
    message = 'JWT missing required content_org filter.'

    def has_permission(self, request, view):
        """
        Ensure that the course_id kwarg provided to the view contains one
        of the organizations specified in the content provider filters
        in the JWT used to authenticate.
        """
        course_key = CourseKey.from_string(view.kwargs.get('course_id'))
        jwt_filters = decode_jwt_filters(request.auth)
        for filter_type, filter_value in jwt_filters:
            if filter_type == 'content_org' and filter_value == course_key.org:
                return True
        log.warning(
            "Permission JwtHasContentOrgFilterForRequestedCourse: no filter found for %s.",
            course_key.org,
        )
        return False


class JwtHasUserFilterForRequestedUser(BasePermission):
    """
    The JWT used to authenticate contains the appropriate user filter for the
    requested user resource.
    """
    message = 'JWT missing required user filter.'

    def has_permission(self, request, view):
        """
        If the JWT has a user filter, verify that the filtered
        user value matches the user in the URL.
        """
        user_filter = self._get_user_filter(request)
        if not user_filter:
            # no user filters are present in the token to limit access
            return True

        username_param = get_username_param(request)
        allowed = user_filter == username_param
        if not allowed:
            log.warning(
                "Permission JwtHasUserFilterForRequestedUser: user_filter %s doesn't match username %s.",
                user_filter,
                username_param,
            )
        return allowed

    def _get_user_filter(self, request):
        jwt_filters = decode_jwt_filters(request.auth)
        for filter_type, filter_value in jwt_filters:
            if filter_type == 'user':
                if filter_value == 'me':
                    filter_value = request.user.username.lower()
                return filter_value
        return None


class LoginRedirectIfUnauthenticated(IsAuthenticated):
    """
    A DRF permission class that will login redirect unauthorized users.

    It can be used to convert a plain Django view that was using @login_required
    into a DRF APIView, which is useful to enable our DRF JwtAuthentication class.

    Requires JwtRedirectToLoginIfUnauthenticatedMiddleware to work.

    """


_NOT_JWT_RESTRICTED_PERMISSIONS = NotJwtRestrictedApplication & (IsStaff | IsUserInUrl)
_JWT_RESTRICTED_PERMISSIONS = (
    JwtRestrictedApplication &
    JwtHasScope &
    JwtHasContentOrgFilterForRequestedCourse &
    JwtHasUserFilterForRequestedUser
)
JWT_RESTRICTED_APPLICATION_OR_USER_ACCESS = (
    IsAuthenticated &
    (_NOT_JWT_RESTRICTED_PERMISSIONS | _JWT_RESTRICTED_PERMISSIONS)
)


def get_username_param(request):
    user_parameter_name = 'username'
    url_username = (
        getattr(request, 'parser_context', {}).get('kwargs', {}).get(user_parameter_name, '') or
        request.GET.get(user_parameter_name, '')
    )
    return url_username.lower()
