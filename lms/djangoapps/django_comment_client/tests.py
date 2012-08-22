from django.contrib.auth.models import User
from django.test import TestCase
from student.models import CourseEnrollment, \
                           replicate_enrollment_save, \
                           replicate_enrollment_delete, \
                           update_user_information, \
                           replicate_user_save
                           
from django.db.models.signals import m2m_changed, pre_delete, pre_save, post_delete, post_save
from django.dispatch.dispatcher import _make_id
import string
import random
from .permissions import has_permission
from .models import Role, Permission

class PermissionsTestCase(TestCase):
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):
        self.course_id = "MITx/6.002x/2012_Fall"

        self.moderator_role = Role.objects.get_or_create(name="Moderator", course_id=self.course_id)[0]
        self.student_role = Role.objects.get_or_create(name="Student", course_id=self.course_id)[0]

        self.student = User.objects.create(username=self.random_str(),
                            password="123456", email="john@yahoo.com")
        self.moderator = User.objects.create(username=self.random_str(),
                            password="123456", email="staff@edx.org")
        self.moderator.is_staff = True
        self.moderator.save()
        self.student_enrollment = CourseEnrollment.objects.create(user=self.student, course_id=self.course_id)
        self.moderator_enrollment = CourseEnrollment.objects.create(user=self.moderator, course_id=self.course_id)

    def tearDown(self):
        self.student_enrollment.delete()
        self.moderator_enrollment.delete()

# Do we need to have this? We shouldn't be deleting students, ever
#        self.student.delete()
#        self.moderator.delete()

    def testDefaultRoles(self):
        self.assertTrue(self.student_role in self.student.roles.all())
        self.assertTrue(self.moderator_role in self.moderator.roles.all())

    def testPermission(self):
        name = self.random_str()
        self.moderator_role.add_permission(name)
        self.assertTrue(has_permission(self.moderator, name, self.course_id))

        self.student_role.add_permission(name)
        self.assertTrue(has_permission(self.student, name, self.course_id))
