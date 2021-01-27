"""
Enrollments Service Tests
"""


from common.djangoapps.course_modes.models import CourseMode
from common.djangoapps.course_modes.tests.factories import CourseModeFactory
from common.djangoapps.student.models import CourseEnrollment
from common.djangoapps.student.tests.factories import UserFactory
from openedx.core.djangoapps.enrollments.services import EnrollmentsService
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class EnrollmentsServiceTests(ModuleStoreTestCase):
    """
    Tests for Enrollments Service
    """
    def setUp(self):
        super().setUp()
        self.service = EnrollmentsService()
        self.course = CourseFactory.create()
        self.course_modes = [CourseMode.HONOR, CourseMode.VERIFIED, CourseMode.AUDIT]
        for x in range(3):
            CourseModeFactory.create(mode_slug=self.course_modes[x], course_id=self.course.id)
            user = UserFactory(username='user{}'.format(x))
            CourseEnrollment.enroll(user, self.course.id, mode=self.course_modes[x])

    def test_get_active_enrollments_by_course(self):
        """
        Test that it returns a list of active enrollments
        """
        enrollments = self.service.get_active_enrollments_by_course(self.course.id)
        self.assertEqual(len(enrollments), 3)
        # At minimum, the function should return the user and mode tied to each enrollment
        for x in range(3):
            self.assertEqual(enrollments[x].user.username, 'user{}'.format(x))
            self.assertEqual(enrollments[x].mode, self.course_modes[x])

    def test_get_active_enrollments_by_course_ignore_inactive(self):
        """
        Test that inactive enrollments are ignored
        """
        inactive_enrollment = CourseEnrollment.objects.get(course_id=self.course.id, user__username='user0')
        inactive_enrollment.is_active = False
        inactive_enrollment.save()
        enrollments = self.service.get_active_enrollments_by_course(self.course.id)
        self.assertEqual(len(enrollments), 2)

    def test_get_active_enrollments_no_enrollments(self):
        """
        Test that an empty list is returned if a course has no enrollments
        """
        new_course = CourseFactory()
        enrollments = self.service.get_active_enrollments_by_course(new_course.id)  # pylint: disable=no-member
        self.assertEqual(len(enrollments), 0)
