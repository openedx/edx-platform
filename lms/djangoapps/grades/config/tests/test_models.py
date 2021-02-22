"""
Tests for the models that control the
persistent grading feature.
"""


import itertools
from unittest.mock import patch

import ddt
from django.conf import settings
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
        super().setUp()
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
            assert PersistentGradesEnabledFlag.feature_enabled() == global_flag
            assert PersistentGradesEnabledFlag.feature_enabled(
                self.course_id_1
            ) == (global_flag and (enabled_for_all_courses or enabled_for_course_1))
            assert PersistentGradesEnabledFlag.feature_enabled(
                self.course_id_2
            ) == (global_flag and enabled_for_all_courses)

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
            assert PersistentGradesEnabledFlag.feature_enabled(self.course_id_1)
            # Prior to TNL-5698, creating a second object would fail due to db constraints
            with persistent_grades_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
                course_id=self.course_id_1,
                enabled_for_course=False
            ):
                assert not PersistentGradesEnabledFlag.feature_enabled(self.course_id_1)

    def test_enable_disable_globally(self):
        """
        Ensures that the flag, once enabled globally, can also be disabled.
        """
        with persistent_grades_feature_flags(
            global_flag=True,
            enabled_for_all_courses=True,
        ):
            assert PersistentGradesEnabledFlag.feature_enabled()
            assert PersistentGradesEnabledFlag.feature_enabled(self.course_id_1)
            with persistent_grades_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
            ):
                assert PersistentGradesEnabledFlag.feature_enabled()
                assert not PersistentGradesEnabledFlag.feature_enabled(self.course_id_1)
                with persistent_grades_feature_flags(
                    global_flag=False,
                ):
                    assert not PersistentGradesEnabledFlag.feature_enabled()
                    assert not PersistentGradesEnabledFlag.feature_enabled(self.course_id_1)
