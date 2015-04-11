"""
tests for the models
"""
from student.models import CourseEnrollment  # pylint: disable=import-error
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    CourseEnrollmentFactory,
    UserFactory,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from .factories import (
    CcxFactory,
    CcxFutureMembershipFactory,
)
from ..models import (
    CcxMembership,
    CcxFutureMembership,
)


class TestCcxMembership(ModuleStoreTestCase):
    """Unit tests for the CcxMembership model
    """

    def setUp(self):
        """common setup for all tests"""
        super(TestCcxMembership, self).setUp()
        self.course = course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        enrollment = CourseEnrollmentFactory.create(course_id=course.id)
        self.enrolled_user = enrollment.user
        self.unenrolled_user = UserFactory.create()

    def create_future_enrollment(self, user, auto_enroll=True):
        """
        utility method to create future enrollment
        """
        pfm = CcxFutureMembershipFactory.create(
            ccx=self.ccx,
            email=user.email,
            auto_enroll=auto_enroll
        )
        return pfm

    def has_course_enrollment(self, user):
        """
        utility method to create future enrollment
        """
        enrollment = CourseEnrollment.objects.filter(
            user=user, course_id=self.course.id
        )
        return enrollment.exists()

    def has_ccx_membership(self, user):
        """
        verify ccx membership
        """
        membership = CcxMembership.objects.filter(
            student=user, ccx=self.ccx, active=True
        )
        return membership.exists()

    def has_ccx_future_membership(self, user):
        """
        verify future ccx membership
        """
        future_membership = CcxFutureMembership.objects.filter(
            email=user.email, ccx=self.ccx
        )
        return future_membership.exists()

    def call_mut(self, student, future_membership):
        """
        Call the method undser test
        """
        CcxMembership.auto_enroll(student, future_membership)

    def test_ccx_auto_enroll_unregistered_user(self):
        """verify auto_enroll works when user is not enrolled in the MOOC

        n.b.  After auto_enroll, user will have both a MOOC enrollment and a
              CCX membership
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))
        # auto_enroll user
        self.call_mut(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_ccx_membership(user))
        self.assertFalse(self.has_ccx_future_membership(user))

    def test_ccx_auto_enroll_registered_user(self):
        """verify auto_enroll works when user is enrolled in the MOOC
        """
        user = self.enrolled_user
        pfm = self.create_future_enrollment(user)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertTrue(self.has_course_enrollment(user))

        self.call_mut(user, pfm)

        self.assertTrue(self.has_course_enrollment(user))
        self.assertTrue(self.has_ccx_membership(user))
        self.assertFalse(self.has_ccx_future_membership(user))

    def test_future_membership_disallows_auto_enroll(self):
        """verify that the CcxFutureMembership can veto auto_enroll
        """
        user = self.unenrolled_user
        pfm = self.create_future_enrollment(user, auto_enroll=False)
        self.assertTrue(self.has_ccx_future_membership(user))
        self.assertFalse(self.has_course_enrollment(user))

        self.assertRaises(ValueError, self.call_mut, user, pfm)

        self.assertFalse(self.has_course_enrollment(user))
        self.assertFalse(self.has_ccx_membership(user))
        self.assertTrue(self.has_ccx_future_membership(user))
