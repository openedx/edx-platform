"""
django-rules and Bridgekeeper rules for course_roles related features
"""
from bridgekeeper.rules import Rule

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import CourseKey
from xblock.core import XBlock

from openedx.core.djangoapps.course_roles.api import get_all_user_permissions_for_a_course
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.toggles import use_permission_checks
from openedx.core.djangoapps.course_roles.models import UserRole
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.course_block import CourseBlock
from openedx.core.djangoapps.django_comment_common.models import Role
from xmodule.error_block import ErrorBlock


class CourseRolesRule(Rule):  # lint-amnesty, pylint: disable=abstract-method
    """
    Base class for course roles rules.
    """
    @staticmethod
    def _get_course_key(instance):
        """
        Get the course key for an instance.
        """
        if isinstance(instance, CourseKey):
            course_key = instance
        elif isinstance(instance, (CourseBlock, CourseOverview)):
            course_key = instance.id
        elif isinstance(instance, (ErrorBlock, XBlock)):
            course_key = instance.scope_ids.usage_id.course_key
        else:
            try:
                course_key = CourseKey.from_string(str(instance))
            except InvalidKeyError as exc:
                raise ValueError(f"Cannot get a CourseKey from intance: {instance}") from exc
        return course_key


class HasPermissionRule(CourseRolesRule):  # lint-amnesty, pylint: disable=abstract-method
    """
    Rule to check if a user has a permission for a course,
    including, if applicable, organization-wide permissions
    and instance-wide permissions.
    """
    def __init__(self, permission: CourseRolesPermission):
        self.permission = permission

    def check(self, user, instance=None):
        if not use_permission_checks():
            return False
        if not user.is_authenticated:
            return False
        if instance is None:
            return UserRole.objects.filter(
                user=user,
                role__permissions__name=self.permission.value.name,
                org__isnull=True,
                course__isnull=True,
            ).exists()
        course_key = self._get_course_key(instance)
        return self.permission in get_all_user_permissions_for_a_course(user, course_key)


class HasForumsRolesRule(CourseRolesRule):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    """
    Rule to check if a user has a forum role for a course.
    """
    def __init__(self, *roles):
        self.roles = roles

    def check(self, user, instance=None):
        if not use_permission_checks():
            return False
        if not user.is_authenticated:
            return False
        if instance is None:
            return False
        course_key = self._get_course_key(instance)
        return Role.user_has_role_for_course(user, course_key, self.roles)
