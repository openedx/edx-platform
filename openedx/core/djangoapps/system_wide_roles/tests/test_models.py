"""
Tests for system wide roles' django models.
"""


from django.test import TestCase
from common.djangoapps.student.tests.factories import UserFactory

from openedx.core.djangoapps.system_wide_roles.models import SystemWideRole, SystemWideRoleAssignment


class SystemWideRoleTests(TestCase):
    """ Tests for SystemWideRole in system_wide_roles app """

    def setUp(self):
        super(SystemWideRoleTests, self).setUp()
        self.role = SystemWideRole.objects.create(name='TestRole')

    def test_str(self):
        self.assertEqual(str(self.role), '<SystemWideRole TestRole>')

    def test_repr(self):
        self.assertEqual(repr(self.role), '<SystemWideRole TestRole>')


class SystemWideRoleAssignmentTests(TestCase):
    """ Tests for SystemWideRoleAssignment in system_wide_roles app """

    def setUp(self):
        super(SystemWideRoleAssignmentTests, self).setUp()
        self.user = UserFactory.create()
        self.role = SystemWideRole.objects.create(name='TestRole')

    def test_str(self):
        role_assignment = SystemWideRoleAssignment.objects.create(role=self.role, user=self.user)
        self.assertEqual(
            str(role_assignment),
            '<SystemWideRoleAssignment for User {user} assigned to role {role}>'.format(
                user=self.user.id, role=self.role.name
            )
        )

    def test_repr(self):
        role_assignment = SystemWideRoleAssignment.objects.create(role=self.role, user=self.user)
        self.assertEqual(
            repr(role_assignment),
            '<SystemWideRoleAssignment for User {user} assigned to role {role}>'.format(
                user=self.user.id, role=self.role.name
            )
        )
