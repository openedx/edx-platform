"""
Tests for configuration models of Adaptive Learning
"""

import ddt

from django.test import TestCase
from opaque_keys.edx.locator import CourseLocator

from adaptive_learning.config.models import AdaptiveLearningEnabledFlag
from adaptive_learning.config.tests.utils import adaptive_learning_enabled_feature_flags


@ddt.ddt
class AdaptiveLearningEnabledFlagTest(TestCase):
    """
    Tests the behaviour of the feature flags for Adaptive Learning
    which are set in Django Admin settings.
    """

    def setUp(self):
        super(AdaptiveLearningEnabledFlagTest, self).setUp()
        self.course_id = CourseLocator(org="edx", course="course", run="run")

    @ddt.data(
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (True, True, True)
    )
    @ddt.unpack
    def test_feature_enabled(
        self, global_enabled_flag, course_enabled_flag, feature_enabled_for_course
    ):
        with adaptive_learning_enabled_feature_flags(
            global_enabled_flag, self.course_id, course_enabled_flag
        ):
            self.assertEqual(
                AdaptiveLearningEnabledFlag.feature_enabled(self.course_id), feature_enabled_for_course
            )
