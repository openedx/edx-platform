from bridgekeeper.rules import Rule

from common.djangoapps.student.roles import CourseLimitedStaffRole


class CourseLimitedStaffRule(Rule):
    label = "course_limited_staff"
    description = "Check if the user has the CourseLimitedStaffRole"

    def check(self, user, course_key):
        return isinstance(
            user.roles.filter(name="CourseLimitedStaff"),
            CourseLimitedStaffRole(course_key),
        )
