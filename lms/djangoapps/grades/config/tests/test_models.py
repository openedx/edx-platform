"""
Tests for the models that control the
persistent grading feature.
"""
import ddt
from django.conf import settings
import itertools
from mock import patch

from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator
from lms.djangoapps.grades.config.models import PersistentGradesEnabledFlag
from lms.djangoapps.grades.config.tests.utils import persistent_grades_feature_flags


@patch.dict(settings.FEATURES, {'PERSISTENT_GRADES_ENABLED_FOR_ALL_TESTS': False})
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

    @ddt.data(*itertools.product(
        (True, False),
        (True, False),
        (True, False),
    ))
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

    def test_enable_disable_course_flag(self):
        """
        Ensures that the flag, once enabled for a course, can also be disabled.
        """
        with persistent_grades_feature_flags(
            global_flag=True,
            enabled_for_all_courses=False,
            course_id=self.course_id_1,
            enabled_for_course=True
        ):
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course_id_1))
            # Prior to TNL-5698, creating a second object would fail due to db constraints
            with persistent_grades_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
                course_id=self.course_id_1,
                enabled_for_course=False
            ):
                self.assertFalse(PersistentGradesEnabledFlag.feature_enabled(self.course_id_1))

    def test_enable_disable_globally(self):
        """
        Ensures that the flag, once enabled globally, can also be disabled.
        """
        with persistent_grades_feature_flags(
            global_flag=True,
            enabled_for_all_courses=True,
        ):
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled())
            self.assertTrue(PersistentGradesEnabledFlag.feature_enabled(self.course_id_1))
            with persistent_grades_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
            ):
                self.assertTrue(PersistentGradesEnabledFlag.feature_enabled())
                self.assertFalse(PersistentGradesEnabledFlag.feature_enabled(self.course_id_1))
                with persistent_grades_feature_flags(
                    global_flag=False,
                ):
                    self.assertFalse(PersistentGradesEnabledFlag.feature_enabled())
                    self.assertFalse(PersistentGradesEnabledFlag.feature_enabled(self.course_id_1))
