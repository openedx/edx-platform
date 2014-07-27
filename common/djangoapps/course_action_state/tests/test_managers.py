"""
Tests for basic common operations related to Course Action State managers
"""
from ddt import ddt, data
from django.test import TestCase
from opaque_keys.edx.locations import CourseLocator
from course_action_state.models import CourseRerunState
from course_action_state.managers import CourseActionStateException


# Sequence of Action models to be tested with ddt.
COURSE_ACTION_STATES = (CourseRerunState, )

class TestCourseActionStateManagerBase(TestCase):
    """
    Base class for testing Course Action State Managers.
    """
    def setUp(self):
        self.course_key = CourseLocator("test_org", "test_course_num", "test_run")


@ddt
class TestCourseActionStateManager(TestCourseActionStateManagerBase):
    """
    Test class for testing the CourseActionStateManager.
    """
    @data(*COURSE_ACTION_STATES)
    def test_update_state_allow_not_found_is_false(self, action_class):
        with self.assertRaises(CourseActionStateException):
            action_class.objects.update_state(self.course_key, "fake_state", allow_not_found=False)

    @data(*COURSE_ACTION_STATES)
    def test_update_state_allow_not_found(self, action_class):
        action_class.objects.update_state(self.course_key, "new_state", allow_not_found=True)
        self.assertIsNotNone(
            action_class.objects.get_for_course(self.course_key)
        )

    @data(*COURSE_ACTION_STATES)
    def test_delete(self, action_class):
        obj = action_class.objects.update_state(self.course_key, "new_state", allow_not_found=True)
        action_class.objects.delete(obj.id)
        self.assertIsNone(
            action_class.objects.get_for_course(self.course_key)
        )


@ddt
class TestCourseActionUIStateManager(TestCourseActionStateManagerBase):
    """
    Test class for testing the CourseActionUIStateManager.
    """
    @data(*COURSE_ACTION_STATES)
    def test_find_all_for_display(self, action_class):
        course_keys = set(
            CourseLocator("test_org", "test_course_num" + str(num), "test_run")
            for num in range(1, 10)
        )
        for course_key in course_keys:
            action_class.objects.update_state(course_key, "new_state", allow_not_found=True)

        found_course_keys = set(action_state.course_key for action_state in action_class.objects.find_all_for_display())
        self.assertSetEqual(course_keys, found_course_keys)
