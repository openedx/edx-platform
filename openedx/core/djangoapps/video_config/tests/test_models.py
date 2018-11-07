"""
Tests for the models that configures HLS Playback feature.
"""
import ddt
import itertools

from contextlib import contextmanager

from django.test import TestCase

from opaque_keys.edx.locator import CourseLocator
from openedx.core.djangoapps.video_config.models import CourseHLSPlaybackEnabledFlag, HLSPlaybackEnabledFlag


@contextmanager
def hls_playback_feature_flags(
        global_flag, enabled_for_all_courses=False,
        course_id=None, enabled_for_course=False
):
    """
    Yields HLS Playback Configuration records for unit tests
    Arguments:
        global_flag (bool): Specifies whether feature is enabled globally
        enabled_for_all_courses (bool): Specifies whether feature is enabled for all courses
        course_id (CourseLocator): Course locator for course specific configurations
        enabled_for_course (bool): Specifies whether feature should be available for a course
    """
    HLSPlaybackEnabledFlag.objects.create(enabled=global_flag, enabled_for_all_courses=enabled_for_all_courses)
    if course_id:
        CourseHLSPlaybackEnabledFlag.objects.create(course_id=course_id, enabled=enabled_for_course)
    yield


@ddt.ddt
class TestHLSPlaybackFlag(TestCase):
    """
    Tests the behavior of the flags for HLS Playback feature.
    These are set via Django admin settings.
    """
    def setUp(self):
        super(TestHLSPlaybackFlag, self).setUp()
        self.course_id_1 = CourseLocator(org="edx", course="course", run="run")
        self.course_id_2 = CourseLocator(org="edx", course="course2", run="run")

    @ddt.data(
        *itertools.product(
            (True, False),
            (True, False),
            (True, False),
        )
    )
    @ddt.unpack
    def test_hls_playback_feature_flags(self, global_flag, enabled_for_all_courses, enabled_for_course_1):
        """
        Tests that the feature flags works correctly on tweaking global flags in combination
        with course-specific flags.
        """
        with hls_playback_feature_flags(
            global_flag=global_flag,
            enabled_for_all_courses=enabled_for_all_courses,
            course_id=self.course_id_1,
            enabled_for_course=enabled_for_course_1
        ):
            self.assertEqual(
                HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1),
                global_flag and (enabled_for_all_courses or enabled_for_course_1)
            )
            self.assertEqual(
                HLSPlaybackEnabledFlag.feature_enabled(self.course_id_2),
                global_flag and enabled_for_all_courses
            )

    def test_enable_disable_course_flag(self):
        """
        Ensures that the flag, once enabled for a course, can also be disabled.
        """
        with hls_playback_feature_flags(
            global_flag=True,
            enabled_for_all_courses=False,
            course_id=self.course_id_1,
            enabled_for_course=True
        ):
            self.assertTrue(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1))
            with hls_playback_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
                course_id=self.course_id_1,
                enabled_for_course=False
            ):
                self.assertFalse(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1))

    def test_enable_disable_globally(self):
        """
        Ensures that the flag, once enabled globally, can also be disabled.
        """
        with hls_playback_feature_flags(
            global_flag=True,
            enabled_for_all_courses=True,
        ):
            self.assertTrue(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1))
            self.assertTrue(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_2))
            with hls_playback_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
            ):
                self.assertFalse(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1))
                self.assertFalse(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_2))
                with hls_playback_feature_flags(
                    global_flag=False,
                ):
                    self.assertFalse(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_1))
                    self.assertFalse(HLSPlaybackEnabledFlag.feature_enabled(self.course_id_2))
