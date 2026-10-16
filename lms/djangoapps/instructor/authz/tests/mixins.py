"""
Test helpers to assign AuthZ roles in Instructor Dashboard tests.
"""

from unittest.mock import patch

from openedx_authz.api.users import assign_role_to_user_in_scope
from openedx_authz.engine.enforcer import AuthzEnforcer

from common.djangoapps.student.tests.factories import UserFactory
from lms.djangoapps.instructor.authz import constants as authz_constants
from openedx.core import toggles as core_toggles
from openedx.core.djangoapps.authz.tests.fixtures import seed_policies

COURSE_SCOPE_POLICY = "course-v1^*"

# TEMPORARY: the role assignments of the Instructor Dashboard permissions depend
# on a separate issue that will define them in openedx-authz. They are seeded
# here only for testing.
_INSTRUCTOR_DASHBOARD_ROLE_PERMISSIONS = (
    authz_constants.COURSES_VIEW_COURSE_INFO,
    authz_constants.COURSES_VIEW_ENROLLMENTS,
    authz_constants.COURSES_ENROLL_LEARNERS,
    authz_constants.COURSES_UNENROLL_LEARNERS,
    authz_constants.COURSES_VIEW_GRADEBOOK,
    authz_constants.COURSES_VIEW_GRADING_CONFIGURATION,
    authz_constants.COURSES_MANAGE_LEARNER_GRADING,
    authz_constants.COURSES_VIEW_LEARNER_EXTENSIONS,
    authz_constants.COURSES_MANAGE_LEARNER_EXTENSIONS,
    authz_constants.COURSES_VIEW_COHORTS,
    authz_constants.COURSES_MANAGE_COHORTS,
)
INSTRUCTOR_DASHBOARD_ROLE_PERMISSIONS = {
    "course_admin": _INSTRUCTOR_DASHBOARD_ROLE_PERMISSIONS,
    "course_staff": _INSTRUCTOR_DASHBOARD_ROLE_PERMISSIONS,
}


def seed_instructor_dashboard_policies():
    """
    Add to the enforcer the policies granted by the Instructor Dashboard.

    They are not part of the static policies that ``seed_policies`` loads.
    """
    enforcer = AuthzEnforcer.get_enforcer()
    for role, permissions in INSTRUCTOR_DASHBOARD_ROLE_PERMISSIONS.items():
        for permission in permissions:
            enforcer.add_policy(f"role^{role}", f"act^{permission}", COURSE_SCOPE_POLICY, "allow")


class InstructorAuthzTestMixin:
    """
    Mixin to test the Instructor Dashboard with the AuthZ flag on or off.

    By default the flag is enabled; call ``set_authz_enabled(False)`` to test
    the legacy behavior. The enforcer is seeded with the static AuthZ policies
    plus the Instructor Dashboard ones.
    """

    def setUp(self):
        super().setUp()
        self.authz_flag_patcher = patch.object(
            core_toggles.AUTHZ_COURSE_AUTHORING_FLAG, "is_enabled", return_value=True
        )
        self.authz_flag_mock = self.authz_flag_patcher.start()
        self.addCleanup(self.authz_flag_patcher.stop)

        seed_policies()
        seed_instructor_dashboard_policies()
        self.addCleanup(AuthzEnforcer.get_enforcer().clear_policy)

    def set_authz_enabled(self, enabled: bool):
        """
        Enable or disable ``authz.enable_course_authoring`` for every course.

        Args:
            enabled (bool): The value of the flag.
        """
        self.authz_flag_mock.return_value = enabled

    def assign_authz_role(self, user, role, course_key):
        """
        Assign an AuthZ role to the user in the course.

        The enforcer policy is reloaded afterwards.

        Args:
            user (User): The user receiving the role.
            role (str): The AuthZ role external key.
            course_key (CourseKey): The course where the role is assigned.
        """
        assign_role_to_user_in_scope(user.username, role, str(course_key))
        AuthzEnforcer.get_enforcer().load_policy()

    def create_user_with_authz_role(self, role, course_key, **kwargs):
        """
        Create a user and assign it an AuthZ role in the course.

        Args:
            role (str): The AuthZ role external key.
            course_key (CourseKey): The course where the role is assigned.
            **kwargs: Extra arguments for ``UserFactory``.

        Returns:
            User: The new user.
        """
        user = UserFactory(**kwargs)
        self.assign_authz_role(user, role, course_key)
        return user
