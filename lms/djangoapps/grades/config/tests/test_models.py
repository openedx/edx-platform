"""
Tests for the models that control the
persistent grading feature.
"""
import ddt

from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags


@ddt.ddt
class PersistentGradesFeatureFlagTests(TestCase):
    """
    Tests the behavior of the feature flags for persistent grading.
    These are set via Django admin settings.
    """
    def setUp(self):
        super(PersistentGradesFeatureFlagTests, self).setUp()
        self.course_id_1 = CourseLocator(org="edx", course="course", run="run")
        self.course_id_2 = CourseLocator(org="edx", course="course2", run="run")

    @ddt.data(
        (True, True, True),
        (True, True, False),
        (True, False, True),
        (True, False, False),
        (False, True, True),
        (False, False, True),
        (False, True, False),
        (False, False, False),
    )
    @ddt.unpack
    def test_persistent_grades_feature_flags(self, global_flag, enabled_for_all_courses, enabled_for_course_1):
        with persistent_grades_feature_flags(
            global_flag=global_flag,
            enabled_for_all_courses=enabled_for_all_courses,
            course_id=self.course_id_1,
            enabled_for_course=enabled_for_course_1
        ):
            self.assertEqual(PersistentGradesEnabledFlag.feature_enabled(), global_flag)
            self.assertEqual(
                PersistentGradesEnabledFlag.feature_enabled(self.course_id_1),
                global_flag and (enabled_for_all_courses or enabled_for_course_1)
            )
            self.assertEqual(
                PersistentGradesEnabledFlag.feature_enabled(self.course_id_2),
                global_flag and enabled_for_all_courses
            )
