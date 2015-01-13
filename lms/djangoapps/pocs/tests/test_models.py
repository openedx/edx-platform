from student.models import CourseEnrollment
from student.roles import CoursePocCoachRole
from student.tests.factories import (
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .factories import (
    PocFactory,
    PocMembershipFactory,
    PocFutureMembershipFactory,
)
from ..models import (
    PocMembership,
    PocFutureMembership,
)


class TestPocMembership(ModuleStoreTestCase):
    """Unit tests for the PocMembership model
    """

    def setUp(self):
        """common setup for all tests"""
        self.course = course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CoursePocCoachRole(course.id)
        role.add_users(coach)
        self.poc = PocFactory(course_id=course.id, coach=coach)
        enrollment = CourseEnrollmentFactory.create(course_id=course.id)
        self.enrolled_user = enrollment.user
        self.unenrolled_user = UserFactory.create()

    def create_future_enrollment(self, user, auto_enroll=True):
        pfm = PocFutureMembershipFactory.create(
            poc=self.poc,
            email=user.email,
            auto_enroll=auto_enroll
        )
        return pfm

    def has_course_enrollment(self, user):
        enrollment = CourseEnrollment.objects.filter(
            user=user, course_id=self.course.id
        )
        return enrollment.exists()

    def has_poc_membership(self, user):
        membership = PocMembership.objects.filter(
            student=user, poc=self.poc, active=True
        )
        return membership.exists()

    def has_poc_future_membership(self, user):
        future_membership = PocFutureMembership.objects.filter(
            email=user.email, poc=self.poc
        )
        return future_membership.exists()

    def call_MUT(self, student, future_membership):
        PocMembership.auto_enroll(student, future_membership)

    def test_poc_auto_enroll_unregistered_user(self):
        """verify auto_enroll works when user is not enrolled in the MOOC

        n.b.  After auto_enroll, user will have both a MOOC enrollment and a
              POC membership
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_poc_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))
        # auto_enroll user
        self.call_MUT(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_poc_membership(user))
        self.assertFalse(self.has_poc_future_membership(user))

    def test_poc_auto_enroll_registered_user(self):
        """verify auto_enroll works when user is enrolled in the MOOC
        """
        user = self.enrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_poc_future_membership(user))
        self.assertTrue(self.has_course_enrollment(user))

        self.call_MUT(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_poc_membership(user))
        self.assertFalse(self.has_poc_future_membership(user))

    def test_future_membership_disallows_auto_enroll(self):
        """verify that the PocFutureMembership can veto auto_enroll
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user, auto_enroll=False)
        self.assertTrue(self.has_poc_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))

        self.assertRaises(ValueError, self.call_MUT, user, pfm)

        self.assertFalse(self.has_course_enrollment(user))
        self.assertFalse(self.has_poc_membership(user))
        self.assertTrue(self.has_poc_future_membership(user))
