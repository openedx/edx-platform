"""
Tests for waffle utils models.
"""

from ddt import data, ddt, unpack
from django.test import TestCase
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.keys import CourseKey

from ..models import WaffleFlagCourseOverrideModel


@ddt
class WaffleFlagCourseOverrideTests(TestCase):
    """
    Tests for the waffle flag course override model.
    """

    WAFFLE_TEST_NAME = "waffle_test_course_override"
    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    OVERRIDE_CHOICES = WaffleFlagCourseOverrideModel.ALL_CHOICES

    # Data format: ( is_enabled, override_choice, expected_result )
    @data((True, OVERRIDE_CHOICES.on, OVERRIDE_CHOICES.on),
          (True, OVERRIDE_CHOICES.off, OVERRIDE_CHOICES.off),
          (False, OVERRIDE_CHOICES.on, OVERRIDE_CHOICES.unset))
    @unpack
    def test_setting_override(self, is_enabled, override_choice, expected_result):
        RequestCache.clear_all_namespaces()
        self.set_waffle_course_override(override_choice, is_enabled)
        override_value = WaffleFlagCourseOverrideModel.override_value(
            self.WAFFLE_TEST_NAME, self.TEST_COURSE_KEY
        )
        assert override_value == expected_result

    def test_setting_override_multiple_times(self):
        RequestCache.clear_all_namespaces()
        self.set_waffle_course_override(self.OVERRIDE_CHOICES.on)
        self.set_waffle_course_override(self.OVERRIDE_CHOICES.off)
        override_value = WaffleFlagCourseOverrideModel.override_value(
            self.WAFFLE_TEST_NAME, self.TEST_COURSE_KEY
        )
        assert override_value == self.OVERRIDE_CHOICES.off

    def set_waffle_course_override(self, override_choice, is_enabled=True):
        WaffleFlagCourseOverrideModel.objects.create(
            waffle_flag=self.WAFFLE_TEST_NAME,
            override_choice=override_choice,
            enabled=is_enabled,
            course_id=self.TEST_COURSE_KEY
        )
