"""
Tests of the course_roles.admin module
"""

from django.urls import reverse

from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.core.djangoapps.course_roles.models import Role
from organizations.models import Organization
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase


class AdminCourseRolesUserRoleTest(SharedModuleStoreTestCase):
    """
    Test the django admin course roles form saving data in db.
    """
    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="test_user_1", password="test", is_staff=True, is_superuser=True)
        self.user.save()
        self.org = Organization.objects.create(
            name='test_org_for_course_roles',
            active=True,
            short_name='test_org_for_course_roles'
        )
        self.course = CourseOverviewFactory(org='test_org_for_course_roles', run='1')
        self.role = Role.objects.create(name='test_role')
        self.fake_org = Organization.objects.create(
            name='fake_test_org_for_course_roles',
            active=True,
            short_name='fake_test_org_for_course_roles'
        )

    def test_course_level_role_creation(self):
        data = {
            'course': str(self.course.id),
            'role': str(self.role.id),
            'org': str(self.org.id),
            'email': self.user.email
        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)
        self.assertRedirects(response, reverse('admin:course_roles_userrole_changelist'))

        # checking the new role created matches expectations
        response = self.client.get(reverse('admin:course_roles_userrole_changelist'))
        self.assertContains(response, 'Select user role to change')
        self.assertContains(response, 'Add user role')
        self.assertContains(response, 'test_role')
        self.assertContains(response, str(self.course.id))
        self.assertContains(response, '1 user role')

        #try adding with same information raise error.
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)
        self.assertContains(response, 'already assigned to the user')

    def test_instance_level_role_creation(self):
        data = {
            'role': str(self.role.id),
            'email': self.user.email,
        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)
        self.assertRedirects(response, reverse('admin:course_roles_userrole_changelist'))

        # checking the new role created matches expectations
        response = self.client.get(reverse('admin:course_roles_userrole_changelist'))
        self.assertContains(response, 'test_role')
        self.assertContains(response, '1 user role')

    def test_org_level_role_creation(self):
        data = {
            'role': str(self.role.id),
            'email': self.user.email,
            'org': str(self.org.id)

        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)
        self.assertRedirects(response, reverse('admin:course_roles_userrole_changelist'))

        # checking the new role created matches expectations
        response = self.client.get(reverse('admin:course_roles_userrole_changelist'))
        self.assertContains(response, 'test_role')
        self.assertContains(response, '1 user role')

    def test_course_level_role_creation_without_org_data(self):
        data = {
            'role': str(self.role.id),
            'email': self.user.email,
            'course': str(self.course.id)
        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)

        # checking the new role created matches expectations
        response = self.client.get(reverse('admin:course_roles_userrole_changelist'))
        self.assertContains(response, 'Select user role to change')
        self.assertContains(response, 'Add user role')
        self.assertContains(response, 'test_role')
        self.assertContains(response, str(self.course.id))
        self.assertContains(response, '1 user role')

    def test_course_level_role_creation_with_invalid_data(self):
        email = 'invalid@email.com'
        data = {
            'course_id': 'fake_course_for_course_roles_testing',
            'role': 'finance_admin',
            'org': 'edxx',
            'email': email
        }

        self.client.login(username=self.user, password='test')

        # Adding new role with invalid data
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)

        # checking new role not added, and errors are shown
        self.assertContains(
            response,
            'Select a valid choice. That choice is not one of the available choices.',
            2,
            200,
            '',
            True
        )
        self.assertContains(
            response,
            f'Email does not exist. Could not find {email}. Please re-enter email address',
            1,
            200,
            '',
            True
        )

    def test_course_level_role_creation_with_valid_course_invalid_org(self):
        data = {
            'course': str(self.course.id),
            'role': str(self.role.id),
            'org': str(self.fake_org.id),
            'email': self.user.email
        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)

        # checking new role not added, and errors are shown
        self.assertContains(
            response,
            'Org name {} ({}) is not valid. Valid name is {}.'.format(
                self.fake_org.name, self.fake_org.short_name, self.org.name
            ),
            1,
            200,
            '',
            True
        )

    def test_course_level_role_creation_with_valid_course_blank_org_that_is_invalid_in_db(self):
        course = CourseOverviewFactory(org='nonexistant_org_for_invalid_tests', run='1')
        data = {
            'course': str(course),
            'role': str(self.role.id),
            'email': self.user.email
        }

        self.client.login(username=self.user, password='test')

        # adding new role from django admin page
        response = self.client.post(reverse('admin:course_roles_userrole_add'), data=data)

        # checking new role not added, and errors are shown
        self.assertContains(
            response,
            'An organization could not be found for {course}'.format(
                course=course
            ),
            1,
            200,
            '',
            True
        )
