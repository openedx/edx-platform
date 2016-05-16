"""
Tests for utils.
./manage.py lms test --verbosity=1 lms/djangoapps/teacher_dashboard   --traceback --settings=labster_test
"""

from django.test.utils import override_settings

from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase, TEST_DATA_SPLIT_MODULESTORE

from ccx.tests.factories import CcxFactory
from ccx_keys.locator import CCXLocator
from student.roles import CourseCcxCoachRole
from student.tests.factories import UserFactory
from lms.djangoapps.teacher_dashboard.utils import has_teacher_access


class HasTeacherAccessTests(ModuleStoreTestCase):
    """
    All tests for the views.py file
    """
    MODULESTORE = TEST_DATA_SPLIT_MODULESTORE

    def setUp(self):
        """
        Set up the test data used in the specific tests
        """
        super(HasTeacherAccessTests, self).setUp()

        self.user = UserFactory.create()

    def make_coach(self, course, coach):
        """
        Create coach user.
        """
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)

    def make_ccx(self, course, coach):
        """
        Create ccx.
        """
        ccx = CcxFactory(course_id=course.id, coach=coach)
        return ccx

    def make_course(self, enable_ccx=True):
        return CourseFactory.create(enable_ccx=enable_ccx, display_name='Test Course')

    def get_course(self, key):
        """
        Get a course for a given key
        """
        with self.store.bulk_operations(key):
            course = self.store.get_course(key)
        return course

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_user_unavailable(self):
        """
        Asserts that an anonymous user cannot access Teacher Dashboard.
        """
        course = self.make_course()
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)

        self.assertFalse(has_teacher_access(None, course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': False},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_teacher_dashboard_is_disabled(self):
        """
        Asserts that users cannot access Teacher Dashboard if it is disabled.
        """
        course = self.make_course()
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)

        self.assertFalse(has_teacher_access(self.user, course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': False},
    )
    def test_ccx_feature_is_disabled(self):
        """
        Asserts that users cannot access Teacher Dashboard if CCX feature is disabled.
        """
        course = self.make_course()
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)

        self.assertFalse(has_teacher_access(self.user, course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_ccx_is_disabled_in_course(self):
        """
        Asserts that users cannot access Teacher Dashboard if CCX is disabled in the course.
        """
        course = self.make_course(enable_ccx=False)
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)

        self.assertFalse(has_teacher_access(self.user, course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_students_cannot_access(self):
        """
        Asserts that students cannot access Teacher Dashboard.
        """
        course = self.make_course()
        ccx = self.make_ccx(course, self.user)

        self.assertFalse(has_teacher_access(self.user, course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_dashboard_invisible_in_ccx(self):
        """
        Asserts that Teacher Dashboard invisible in CCX.
        """
        course = self.make_course()
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)
        ccx_key = CCXLocator.from_course_locator(course.id, ccx.id)
        ccx_course = self.get_course(ccx_key)

        self.assertFalse(has_teacher_access(self.user, ccx_course))

    @override_settings(
        LABSTER_FEATURES={'ENABLE_TEACHER_DASHBOARD': True},
        FEATURES={'CUSTOM_COURSES_EDX': True},
    )
    def test_coach_can_access(self):
        """
        Asserts that coach can access Teacher Dashboard.
        """
        course = self.make_course()
        self.make_coach(course, self.user)
        ccx = self.make_ccx(course, self.user)

        self.assertTrue(has_teacher_access(self.user, course))
