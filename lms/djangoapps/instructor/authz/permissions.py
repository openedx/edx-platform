"""
DRF permission class to enforce AuthZ in the Instructor Dashboard views.
"""

import logging
from collections.abc import Mapping

from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from rest_framework.permissions import BasePermission

from common.djangoapps.student.roles import enable_authz_course_authoring
from lms.djangoapps.instructor.authz.helpers import user_has_any_instructor_permission, user_has_instructor_permission
from lms.djangoapps.instructor.authz.legacy import bridgekeeper_check

log = logging.getLogger(__name__)


class InstructorAuthzPermission(BasePermission):
    """
    Replacement of ``InstructorPermission`` for views migrated to AuthZ.

    It is a drop-in replacement of
    ``lms.djangoapps.instructor.permissions.InstructorPermission``.

    With ``authz.enable_course_authoring`` enabled for the course only AuthZ is
    consulted; legacy roles are ignored.

    Attributes expected in the view:
        authz_permissions (str | Collection[str] | Mapping[str, str | Collection[str]]):
            The AuthZ permission identifier required, a collection of them when
            holding any one is enough, or a mapping of HTTP method to either
            when the view needs a different permission per method. Methods
            missing from the mapping are denied with
            ``authz.enable_course_authoring`` enabled for the course.
        permission_name (str): The legacy ``bridgekeeper`` permission, the one
            ``InstructorPermission`` uses. It is enforced when
            ``authz.enable_course_authoring`` is disabled for the course.
        legacy_permission_check (Callable[[User, CourseKey], bool]): Optional.
            Replaces the ``permission_name`` check, for legacy rules that are
            not a bridgekeeper permission.
    """

    def has_permission(self, request, view):
        """
        Check whether the user holds the permission the view requires.

        Args:
            request (Request): The DRF request.
            view (APIView): The view, with ``authz_permissions`` and the legacy
                permission attributes.

        Returns:
            bool: True if access is granted.

        Raises:
            Http404: If the ``course_id`` kwarg of the view is not a valid
                course key.
            ImproperlyConfigured: If the view does not define
                ``authz_permissions``.
        """
        try:
            course_key = CourseKey.from_string(view.kwargs.get("course_id"))
        except InvalidKeyError as exc:
            raise Http404("Invalid course key") from exc

        authz_permissions = getattr(view, "authz_permissions", None)
        if authz_permissions is None:
            raise ImproperlyConfigured(f"{type(view).__name__} must define 'authz_permissions'.")
        if isinstance(authz_permissions, Mapping):
            authz_permissions = authz_permissions.get(request.method)

        legacy_check = getattr(view, "legacy_permission_check", None)
        if legacy_check is None and getattr(view, "permission_name", None):
            legacy_check = bridgekeeper_check(view.permission_name)

        if authz_permissions is None:
            if enable_authz_course_authoring(course_key):
                # Fail closed: a method without an AuthZ permission is never allowed by AuthZ.
                log.warning(
                    "%s %s has no AuthZ permission, denying access",
                    type(view).__name__,
                    request.method,
                    extra={"course_key": str(course_key)},
                )
                return False
            return bool(legacy_check and legacy_check(request.user, course_key))
        if isinstance(authz_permissions, str):
            return user_has_instructor_permission(request.user, authz_permissions, course_key, legacy_check)
        return user_has_any_instructor_permission(request.user, authz_permissions, course_key, legacy_check)
