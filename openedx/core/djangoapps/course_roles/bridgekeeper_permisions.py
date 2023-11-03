# Bridgekeeper permissions for course roles

from bridgekeeper import perms

from lms.djangoapps.courseware.rules import HasRolesRule
from openedx.core.djangoapps.course_roles.permissions import CourseRolesPermission
from openedx.core.djangoapps.course_roles.rules import HasPermissionRule


perms[f'course_roles.{CourseRolesPermission.MANAGE_CONTENT.value}'] = (
    HasRolesRule('staff', 'instructor')
    | HasPermissionRule(CourseRolesPermission.MANAGE_CONTENT.value)
)
