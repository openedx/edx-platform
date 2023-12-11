from bridgekeeper.mixins import BasePermissionMixin

from .rules import CourseLimitedStaffRule


class CourseLimitedStaffRolePermission(BasePermissionMixin):
    label = "CourseLimitedStaffRolePermission"
    description = "Permission to check access to course limited staff"

    def check(self, user, course_key):
        return CourseLimitedStaffRule.check(user, course_key)
