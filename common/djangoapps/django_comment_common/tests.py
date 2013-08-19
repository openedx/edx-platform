from django.test import TestCase

from django_comment_common.models import Role
from student.models import CourseEnrollment, User

class RoleAssignmentTest(TestCase):
    """
    Basic checks to make sure our Roles get assigned and unassigned as students
    are enrolled and unenrolled from a course.
    """

    def setUp(self):
        self.staff_user = User.objects.create_user(
            "patty",
            "patty@fake.edx.org",
        )
        self.staff_user.is_staff = True

        self.student_user = User.objects.create_user(
            "hacky",
            "hacky@fake.edx.org"
        )
        self.course_id = "edX/Fake101/2012"
        CourseEnrollment.enroll(self.staff_user, self.course_id)
        CourseEnrollment.enroll(self.student_user, self.course_id)

    def test_enrollment_auto_role_creation(self):
        moderator_role = Role.objects.get(
            course_id=self.course_id,
            name="Moderator"
        )
        student_role = Role.objects.get(
            course_id=self.course_id,
            name="Student"
        )
        self.assertIn(moderator_role, self.staff_user.roles.all())

        self.assertIn(student_role, self.student_user.roles.all())
        self.assertNotIn(moderator_role, self.student_user.roles.all())

    # The following was written on the assumption that unenrolling from a course
    # should remove all forum Roles for that student for that course. This is
    # not necessarily the case -- please see comments at the top of 
    # django_comment_client.models.assign_default_role(). Leaving it for the
    # forums team to sort out.
    #
    # def test_unenrollment_auto_role_removal(self):
    #     another_student = User.objects.create_user("sol", "sol@fake.edx.org")
    #     CourseEnrollment.enroll(another_student, self.course_id)
    #
    #     CourseEnrollment.unenroll(self.student_user, self.course_id)
    #     # Make sure we didn't delete the actual Role
    #     student_role = Role.objects.get(
    #         course_id=self.course_id,
    #         name="Student"
    #     )
    #     self.assertNotIn(student_role, self.student_user.roles.all())
    #     self.assertIn(student_role, another_student.roles.all())
