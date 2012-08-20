from django.contrib.auth.models import User
from django.utils import unittest
from student.models import CourseEnrollment
                           
from django.db.models.signals import m2m_changed, pre_delete, pre_save, post_delete, post_save
from django.dispatch.dispatcher import _make_id
import string
import random
from .permissions import has_permission, assign_default_role
from .models import Role, Permission


class PermissionsTestCase(unittest.TestCase):
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):

        sender_receivers_to_keep = [
            (assign_default_role, CourseEnrollment),
        ]
        super(PermissionsTestCase, self).setUp(sender_receivers_to_keep=sender_receivers_to_keep)

        self.course_id = "MITx/6.002x/2012_Fall"

        self.moderator_role = Role.objects.get_or_create(name="Moderator", course_id=self.course_id)[0]
        self.student_role = Role.objects.get_or_create(name="Student", course_id=self.course_id)[0]

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
