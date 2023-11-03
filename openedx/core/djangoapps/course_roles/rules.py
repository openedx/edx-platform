from bridgekeeper.rules import Rule

from opaque_keys.edx.keys import CourseKey
from xblock.core import XBlock

from openedx.core.djangoapps.course_roles.helpers import course_or_organization_or_instance_permission_check
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from xmodule.course_block import CourseBlock  # lint-amnesty, pylint: disable=wrong-import-order
from xmodule.error_block import ErrorBlock  # lint-amnesty, pylint: disable=wrong-import-order


class HasPermissionRule(Rule):  # lint-amnesty, pylint: disable=abstract-method, missing-class-docstring
    def __init__(self, permission):
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

        return course_or_organization_or_instance_permission_check(user, self.permission, course_key, course_key.org)
