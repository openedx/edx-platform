"""
Test Student api.py
"""

from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from common.djangoapps.student.api import is_user_enrolled_in_course
from common.djangoapps.student.tests.factories import CourseEnrollmentFactory, UserFactory


class TestStudentApi(SharedModuleStoreTestCase):
    """
    Tests for functionality in the api.py file of the Student django app.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.course = CourseFactory.create()

    def setUp(self):
        super().setUp()
        self.user = UserFactory.create()
        self.course_run_key = self.course.id

    def test_is_user_enrolled_in_course(self):
        """
        Verify the correct value is returned when a learner is actively enrolled in a course-run.
        """
        CourseEnrollmentFactory.create(
            user_id=self.user.id,
            course_id=self.course.id
        )

        result = is_user_enrolled_in_course(self.user, self.course_run_key)
        assert result

    def test_is_user_enrolled_in_course_not_active(self):
        """
        Verify the correct value is returned when a learner is not actively enrolled in a course-run.
        """
        CourseEnrollmentFactory.create(
            user_id=self.user.id,
            course_id=self.course.id,
            is_active=False
        )

        result = is_user_enrolled_in_course(self.user, self.course_run_key)
        assert not result

    def test_is_user_enrolled_in_course_no_enrollment(self):
        """
        Verify the correct value is returned when a learner is not enrolled in a course-run.
        """
        result = is_user_enrolled_in_course(self.user, self.course_run_key)
        assert not result
