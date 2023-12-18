"""
Tests of the course_roles.rules module
"""
from organizations.tests.factories import OrganizationFactory

from edx_toggles.toggles.testutils import override_waffle_flag
from common.djangoapps.student.tests.factories import UserFactory
from opaque_keys.edx.keys import CourseKey
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.models import (
    Permission,
    Role,
    Service,
    UserRole
)
from openedx.core.djangoapps.course_roles.toggles import USE_PERMISSION_CHECKS_FLAG
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CourseRolesRulesTestCase(SharedModuleStoreTestCase):
    """
    Integration tests for course roles rules.
    """
    @classmethod
    def setUpClass(cls):  # pylint: disable=super-method-not-called
        with super().setUpClassAndTestData():
            cls.organization_1_name = "test_organization_1"
            cls.course_1 = CourseFactory.create(
                display_name="test course 1", run="Testing_course_1", org=cls.organization_1_name
            )
            cls.course_1_key = CourseKey.from_string(str(cls.course_1.id))

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.organization_1 = OrganizationFactory(name=cls.organization_1_name)
        CourseOverview.load_from_module_store(cls.course_1_key)
        cls.user_1 = UserFactory(username="test_user_1")
        cls.role_1 = Role.objects.create(name="test_role_1")
        cls.service = Service.objects.create(name="test_service")
        cls.role_1.services.add(cls.service)
        cls.permission_1 = CourseRolesPermission.MANAGE_CONTENT
        permission_1 = Permission.objects.create(name=cls.permission_1.value.name)
        cls.role_1.permissions.add(permission_1)

    @override_waffle_flag(USE_PERMISSION_CHECKS_FLAG, active=True)
    def test_rules(self):
        UserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        assert self.user_1.has_perm(f'course_roles.{self.permission_1.value.name}', self.course_1_key)
        UserRole.objects.create(
            user=self.user_1, role=self.role_1
        )
        assert self.user_1.has_perm(f'course_roles.{self.permission_1.value.name}')
