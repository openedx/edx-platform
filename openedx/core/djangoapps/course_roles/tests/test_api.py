"""
Tests of the course_roles.helpers module
"""
import ddt
from organizations.tests.factories import OrganizationFactory
import pytest

from opaque_keys.edx.keys import CourseKey

from common.djangoapps.student.tests.factories import AnonymousUserFactory, UserFactory
from openedx.core.djangoapps.content.course_overviews.models import CourseOverview
from openedx.core.djangoapps.course_roles.api import (
    get_all_user_permissions_for_a_course,
)
from openedx.core.djangoapps.course_roles.data import CourseRolesPermission
from openedx.core.djangoapps.course_roles.models import (
    Permission,
    Role,
    Service,
    UserRole
)
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class GetAllUserPermissionsTestcase(SharedModuleStoreTestCase):
    """
    Tests of get_all_user_permissions_for_a_course function in course_roles.helpers module
    """
    @classmethod
    def setUpClass(cls):
        with super().setUpClassAndTestData(): # pylint: disable=super-method-not-called
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
        cls.anonymous_user = AnonymousUserFactory()
        cls.user_1 = UserFactory(username="test_user_1")
        cls.user_2 = UserFactory(username="test_user_2")
        cls.role_1 = Role.objects.create(name="test_role_1")
        cls.role_2 = Role.objects.create(name="test_role_2")
        cls.role_3 = Role.objects.create(name="test_role_3")
        cls.role_4 = Role.objects.create(name="test_role_4")
        cls.role_5 = Role.objects.create(name="test_role_5")
        cls.service = Service.objects.create(name="test_service")
        cls.role_1.services.add(cls.service)
        cls.role_2.services.add(cls.service)
        cls.role_3.services.add(cls.service)
        cls.role_4.services.add(cls.service)
        cls.role_5.services.add(cls.service)
        cls.permission_1 = CourseRolesPermission.MANAGE_CONTENT
        cls.permission_2 = CourseRolesPermission.MANAGE_COURSE_SETTINGS
        cls.permission_3 = CourseRolesPermission.MANAGE_ADVANCED_SETTINGS
        cls.permission_4 = CourseRolesPermission.VIEW_ALL_CONTENT
        cls.permission_5 = CourseRolesPermission.VIEW_ONLY_LIVE_PUBLISHED_CONTENT
        permission_1 = Permission.objects.create(name=cls.permission_1.value.name)
        permission_2 = Permission.objects.create(name=cls.permission_2.value.name)
        permission_3 = Permission.objects.create(name=cls.permission_3.value.name)
        permission_4 = Permission.objects.create(name=cls.permission_4.value.name)
        permission_5 = Permission.objects.create(name=cls.permission_5.value.name)
        cls.role_1.permissions.add(permission_1)
        cls.role_2.permissions.add(permission_2)
        cls.role_3.permissions.add(permission_3)
        cls.role_4.permissions.add(permission_4)
        cls.role_5.permissions.add(permission_5)

    def test_get_all_user_permissions_for_a_course_with_anonymus_user(self):
        """
        Test that get_all_user_permissions_for_a_course returns an empty set when the user is anonymous
        """
        assert not get_all_user_permissions_for_a_course(self.anonymous_user, self.course_1_key)

    def test_get_all_user_permissions_for_a_course(self):
        """
        Test that get_all_user_permissions_for_a_course returns the correct permissions for the user and course
        """
        UserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        UserRole.objects.create(
            user=self.user_2, role=self.role_4, course_id=self.course_1.id, org=self.organization_1
        )
        # Test that the correct permissions are returned for user_1
        assert get_all_user_permissions_for_a_course(self.user_1, self.course_1_key) == {self.permission_1}
        UserRole.objects.create(
            user=self.user_1, role=self.role_2, course_id=self.course_1.id, org=self.organization_1
        )
        self.clear_caches()
        # Test that the correct permissions are returned for user_1
        assert get_all_user_permissions_for_a_course(self.user_1, self.course_1_key) == {
            self.permission_1, self.permission_2}

        UserRole.objects.create(
            user=self.user_1, role=self.role_3, org=self.organization_1
        )
        self.clear_caches()
        # Test that the correct permissions are returned for user_1, including org level permissions
        assert get_all_user_permissions_for_a_course(self.user_1, self.course_1_key) == {
            self.permission_1, self.permission_2, self.permission_3}
        UserRole.objects.create(
            user=self.user_1, role=self.role_5
        )
        self.clear_caches()
        # Test that the correct permissions are returned for user_1, including instance level permissions
        assert get_all_user_permissions_for_a_course(self.user_1, self.course_1_key) == {
            self.permission_1, self.permission_2, self.permission_3, self.permission_5}

    def test_get_all_user_permissions_for_a_course_with_no_permissions(self):
        """
        Test that get_all_user_permissions_for_a_course returns an empty list when the user has no permissions
        """
        assert not get_all_user_permissions_for_a_course(self.user_1, self.course_1_key)

    @ddt.data(
        (None, 1),
        (1, None),
        (None, None),
    )
    @ddt.unpack
    def test_get_all_user_permissions_for_a_course_with_none_values(self, user_id, course_key):
        """
        Test that get_all_user_permissions_for_a_course raises value error when the user or course_key is None
        """
        with pytest.raises(TypeError):
            get_all_user_permissions_for_a_course(user_id, course_key)

    def test_get_all_user_permissions_for_a_course_with_invalid_course(self):
        """
        Test that get_all_user_permissions_for_a_course raises value error when the course not exist
        """
        with pytest.raises(ValueError):
            get_all_user_permissions_for_a_course(self.user_1, CourseKey.from_string("course-v1:org+course+run"))

    def test_number_of_queries(self):
        """
        Test the number of queries executed by get_all_user_permissions_for_a_course
        """
        UserRole.objects.create(
            user=self.user_1, role=self.role_1, course_id=self.course_1.id, org=self.organization_1
        )
        with self.assertNumQueries(2):
            get_all_user_permissions_for_a_course(self.user_1, self.course_1_key)
        # Test that the number of queries is 0 when the request are cached
        with self.assertNumQueries(0):
            get_all_user_permissions_for_a_course(self.user_1, self.course_1_key)
