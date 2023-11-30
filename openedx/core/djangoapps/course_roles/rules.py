"""
django-rules and Bridgekeeper rules for course_roles related features
"""
from bridgekeeper.rules import Rule

from opaque_keys.edx.keys import CourseKey
from xblock.core import XBlock

from openedx.core.djangoapps.course_roles.api import get_all_user_permissions_for_a_course
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.course_block import CourseBlock
from openedx.core.djangoapps.django_comment_common.models import Role
from xmodule.error_block import ErrorBlock


class HasPermissionRule(Rule):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    """
    Rule to check if a user has a permission for a course,
    including, if applicable, organization-wide permissions
    and instance-wide permissions.
    """
    def __init__(self, permission: CourseRolesPermission):
        self.permission = permission

    def check(self, user, instance=None):
        if not user.is_authenticated:
            return False
        if isinstance(instance, CourseKey):
            course_key = instance
        elif isinstance(instance, (CourseBlock, CourseOverview)):
            course_key = instance.id
        elif isinstance(instance, (ErrorBlock, XBlock)):
            course_key = instance.scope_ids.usage_id.course_key
        else:
            course_key = CourseKey.from_string(str(instance))

        return self.permission in get_all_user_permissions_for_a_course(user, course_key)


class HasForumsRolesRule(Rule):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    """
    Rule to check if a user has a forum role for a course.
    """
    def __init__(self, *roles):
        self.role = roles

    def check(self, user, instance=None):
        if not user.is_authenticated:
            return False
        if isinstance(instance, CourseKey):
            course_key = instance
        elif isinstance(instance, (CourseBlock, CourseOverview)):
            course_key = instance.id
        elif isinstance(instance, (ErrorBlock, XBlock)):
            course_key = instance.scope_ids.usage_id.course_key
        else:
            course_key = CourseKey.from_string(str(instance))

        return Role.user_has_role_for_course(user, course_key, self.roles)
