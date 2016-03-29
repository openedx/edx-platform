"""
Tests of various permissions levels for the comment client
"""
import string
import random
from unittest import skip

from django.contrib.auth.models import User
from django.test import TestCase

from student.models import CourseEnrollment
from django_comment_client.permissions import has_permission
from django_comment_common.models import Role


@skip('TNL-4284')  # TODO fix these. TNL-4284
class PermissionsTestCase(TestCase):
    """Tests for comment client roles and permissions."""
    def random_str(self, length=15, chars=string.ascii_uppercase + string.digits):
        """Return random strings for use as names."""
        return ''.join(random.choice(chars) for x in range(length))

    def setUp(self):
        super(PermissionsTestCase, self).setUp()

        self.course_id = "edX/toy/2012_Fall"

        self.moderator_role = Role.objects.get_or_create(name="Moderator", course_id=self.course_id)[0]
        self.student_role = Role.objects.get_or_create(name="Student", course_id=self.course_id)[0]

        self.student = User.objects.create(username=self.random_str(),
                                           password="123456", email="john@yahoo.com")
        self.moderator = User.objects.create(username=self.random_str(),
                                             password="123456", email="staff@edx.org")
        self.moderator.is_staff = True
        self.moderator.save()
        self.student_enrollment = CourseEnrollment.enroll(self.student, self.course_id)
        self.addCleanup(self.student_enrollment.delete)
        self.moderator_enrollment = CourseEnrollment.enroll(self.moderator, self.course_id)
        self.addCleanup(self.moderator_enrollment.delete)
        # Do we need to have this in a cleanup? We shouldn't be deleting students, ever.
        #   self.student.delete()
        #   self.moderator.delete()

    def test_default_roles(self):
        self.assertIn(self.student_role, self.student.roles.all())
        self.assertIn(self.moderator_role, self.moderator.roles.all())

    def test_add_permission(self):
        name = self.random_str()
        self.moderator_role.add_permission(name)
        self.assertTrue(has_permission(self.moderator, name, self.course_id))

        self.student_role.add_permission(name)
        self.assertTrue(has_permission(self.student, name, self.course_id))
