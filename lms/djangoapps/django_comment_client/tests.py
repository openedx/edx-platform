from django.contrib.auth.models import User
from django.utils import unittest
import string
import random
from .permissions import student_role, moderator_role, add_permission, has_permission
from .models import Role, Permission


class PermissionsTestCase(unittest.TestCase):
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):
        self.student = User.objects.create(username=self.random_str(),
                            password="123456", email="john@yahoo.com")
        self.moderator = User.objects.create(username=self.random_str(),
                            password="123456", email="staff@edx.org")
        self.moderator.is_staff = True
        self.moderator.save()

    def tearDown(self):
        self.student.delete()
        self.moderator.delete()

    def testDefaultRoles(self):
        self.assertTrue(student_role in self.student.roles.all())
        self.assertTrue(moderator_role in self.moderator.roles.all())

    def testPermission(self):
        name = self.random_str()
        Permission.register(name)
        add_permission(moderator_role, name)
        self.assertTrue(has_permission(self.moderator, name))

        add_permission(self.student, name)
        self.assertTrue(has_permission(self.student, name))