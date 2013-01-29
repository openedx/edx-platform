import django_comment_client.models as models
import django_comment_client.permissions as permissions
from django.test import TestCase
from nose.plugins.skip import SkipTest
from courseware.courses import get_course_by_id

class RoleClassTestCase(TestCase):
    def setUp(self):
        self.course_id = "edX/toy/2012_Fall"
        self.student_role = models.Role.objects.create(name="Student",
                                                       course_id=self.course_id)

    def test_unicode(self):
        self.assertEqual(str(self.student_role), "Student for edX/toy/2012_Fall")

        self.admin_for_all = models.Role.objects.create(name="Administrator")
        self.assertEqual(str(self.admin_for_all), "Administrator for all courses")

    def test_has_permission(self):
        self.student_role.add_permission("delete_thread")
        self.TA_role = models.Role.objects.create(name="Community TA",
                                                  course_id=self.course_id)
        self.assertTrue(self.student_role.has_permission("delete_thread"))
        self.assertFalse(self.TA_role.has_permission("delete_thread"))

    # Toy course does not have a blackout period defined.
    def test_students_can_create_if_not_during_blackout(self):
        self.student_role.add_permission("create_comment")
        self.assertTrue(self.student_role.has_permission("create_comment"))

    def test_students_cannot_create_during_blackout(self):
        # Not sure how to set up these conditions
        raise SkipTest()

    def test_inherit_permissions(self):
        self.student_role.add_permission("delete_thread")
        self.TA_role = models.Role.objects.create(name="Community TA",
                                                  course_id=self.course_id)
        self.TA_role.inherit_permissions(self.student_role)
        self.assertTrue(self.TA_role.has_permission("delete_thread"))

    # TODO: You should not be able to inherit permissions across courses?
    def test_inherit_permissions_across_courses(self):
        raise SkipTest()
        self.student_role.add_permission("delete_thread")
        self.course_id_2 = "MITx/6.002x/2012_Fall"
        self.admin_role = models.Role.objects.create(name="Administrator",
                                                     course_id=self.course_id_2)
        self.admin_role.inherit_permissions(self.student_role)

class PermissionClassTestCase(TestCase):
    def test_unicode(self):
        self.permission = permissions.Permission.objects.create(name="test")
        self.assertEqual(str(self.permission), "test")
