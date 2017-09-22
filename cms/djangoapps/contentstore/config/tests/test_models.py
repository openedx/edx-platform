"""
Tests for the models that control the
persistent grading feature.
"""
import itertools

import ddt
from django.conf import settings
from django.test import TestCase
from mock import patch
from opaque_keys.edx.locator import CourseLocator

from contentstore.config.models import NewAssetsPageFlag
from contentstore.config.tests.utils import new_assets_page_feature_flags


@ddt.ddt
class NewAssetsPageFlagTests(TestCase):
    """
    Tests the behavior of the feature flags for the new assets page.
    These are set via Django admin settings.
    """
    def setUp(self):
        super(NewAssetsPageFlagTests, self).setUp()
        self.course_id_1 = CourseLocator(org="edx", course="course", run="run")
        self.course_id_2 = CourseLocator(org="edx", course="course2", run="run")

    @ddt.data(*itertools.product(
        (True, False),
        (True, False),
        (True, False),
    ))
    @ddt.unpack
    def test_new_assets_page_feature_flags(self, global_flag, enabled_for_all_courses, enabled_for_course_1):
        with new_assets_page_feature_flags(
            global_flag=global_flag,
            enabled_for_all_courses=enabled_for_all_courses,
            course_id=self.course_id_1,
            enabled_for_course=enabled_for_course_1
        ):
            self.assertEqual(NewAssetsPageFlag.feature_enabled(), global_flag and enabled_for_all_courses)
            self.assertEqual(
                NewAssetsPageFlag.feature_enabled(self.course_id_1),
                global_flag and (enabled_for_all_courses or enabled_for_course_1)
            )
            self.assertEqual(
                NewAssetsPageFlag.feature_enabled(self.course_id_2),
                global_flag and enabled_for_all_courses
            )

    def test_enable_disable_course_flag(self):
        """
        Ensures that the flag, once enabled for a course, can also be disabled.
        """
        with new_assets_page_feature_flags(
            global_flag=True,
            enabled_for_all_courses=False,
            course_id=self.course_id_1,
            enabled_for_course=True
        ):
            self.assertTrue(NewAssetsPageFlag.feature_enabled(self.course_id_1))
            with new_assets_page_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
                course_id=self.course_id_1,
                enabled_for_course=False
            ):
                self.assertFalse(NewAssetsPageFlag.feature_enabled(self.course_id_1))

    def test_enable_disable_globally(self):
        """
        Ensures that the flag, once enabled globally, can also be disabled.
        """
        with new_assets_page_feature_flags(
            global_flag=True,
            enabled_for_all_courses=True,
        ):
            self.assertTrue(NewAssetsPageFlag.feature_enabled())
            self.assertTrue(NewAssetsPageFlag.feature_enabled(self.course_id_1))
            with new_assets_page_feature_flags(
                global_flag=True,
                enabled_for_all_courses=False,
                course_id=self.course_id_1,
                enabled_for_course=True
            ):
                self.assertFalse(NewAssetsPageFlag.feature_enabled())
                self.assertTrue(NewAssetsPageFlag.feature_enabled(self.course_id_1))
                with new_assets_page_feature_flags(
                    global_flag=False,
                ):
                    self.assertFalse(NewAssetsPageFlag.feature_enabled())
                    self.assertFalse(NewAssetsPageFlag.feature_enabled(self.course_id_1))
