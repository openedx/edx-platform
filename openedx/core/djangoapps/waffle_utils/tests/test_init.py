"""
Tests for waffle utils features.
"""

import crum
import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from django.test.utils import override_settings
from edx_django_utils.cache import RequestCache
from mock import patch
from opaque_keys.edx.keys import CourseKey
from waffle.testutils import override_flag

from .. import (
    CourseWaffleFlag,
    WaffleFlagNamespace,
    WaffleSwitchNamespace,
)
from ..models import WaffleFlagCourseOverrideModel


@ddt.ddt
class TestCourseWaffleFlag(TestCase):
    """
    Tests the CourseWaffleFlag.
    """

    NAMESPACE_NAME = "test_namespace"
    FLAG_NAME = "test_flag"
    NAMESPACED_FLAG_NAME = NAMESPACE_NAME + "." + FLAG_NAME
    FLAG_2_NAME = "test_flag_2"
    NAMESPACED_FLAG_2_NAME = NAMESPACE_NAME + "." + FLAG_2_NAME

    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    TEST_COURSE_2_KEY = CourseKey.from_string("edX/DemoX/Demo_Course_2")
    TEST_NAMESPACE = WaffleFlagNamespace(NAMESPACE_NAME)
    TEST_COURSE_FLAG = CourseWaffleFlag(TEST_NAMESPACE, FLAG_NAME, __name__)

    def setUp(self):
        super().setUp()
        request = RequestFactory().request()
        self.addCleanup(crum.set_current_request, None)
        crum.set_current_request(request)
        RequestCache.clear_all_namespaces()

    @override_settings(WAFFLE_FLAG_CUSTOM_ATTRIBUTES=[NAMESPACED_FLAG_NAME])
    @ddt.data(
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.on, 'waffle_enabled': False, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.off, 'waffle_enabled': True, 'result': False},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': True, 'result': True},
        {'course_override': WaffleFlagCourseOverrideModel.ALL_CHOICES.unset, 'waffle_enabled': False, 'result': False},
    )
    def test_course_waffle_flag(self, data):
        """
        Tests various combinations of a flag being set in waffle and overridden
        for a course.
        """
        with patch.object(WaffleFlagCourseOverrideModel, 'override_value', return_value=data['course_override']):
            with override_flag(self.NAMESPACED_FLAG_NAME, active=data['waffle_enabled']):
                # check twice to test that the result is properly cached
                self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY), data['result'])
                self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY), data['result'])
                # result is cached, so override check should happen once
                # pylint: disable=no-member
                WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                    self.NAMESPACED_FLAG_NAME,
                    self.TEST_COURSE_KEY
                )

        # check flag for a second course
        if data['course_override'] == WaffleFlagCourseOverrideModel.ALL_CHOICES.unset:
            # When course override wasn't set for the first course, the second course will get the same
            # cached value from waffle.
            second_value = data['waffle_enabled']
            self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), second_value)
        else:
            # When course override was set for the first course, it should not apply to the second
            # course which should get the default value of False.
            second_value = False
            self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), second_value)

    @override_settings(WAFFLE_FLAG_CUSTOM_ATTRIBUTES=[NAMESPACED_FLAG_NAME])
    def test_undefined_waffle_flag(self):
        """
        Test flag with undefined waffle flag.
        """
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            __name__,
        )

        with patch.object(
            WaffleFlagCourseOverrideModel,
            'override_value',
            return_value=WaffleFlagCourseOverrideModel.ALL_CHOICES.unset
        ):
            # check twice to test that the result is properly cached
            self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), False)
            self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), False)
            # result is cached, so override check should happen once
            # pylint: disable=no-member
            WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                self.NAMESPACED_FLAG_NAME,
                self.TEST_COURSE_KEY
            )

    def test_without_request_and_undefined_waffle(self):
        """
        Test the flag behavior when outside a request context and waffle data undefined.
        """
        crum.set_current_request(None)
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            __name__,
        )
        self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), False)

    def test_without_request_and_everyone_active_waffle(self):
        """
        Test the flag behavior when outside a request context and waffle active for everyone.
        """
        crum.set_current_request(None)
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            __name__,
        )
        with override_flag(self.NAMESPACED_FLAG_NAME, active=True):
            self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), True)


class DeprecatedWaffleFlagTests(TestCase):
    """
    Tests for the deprecated waffle methods, including override and import paths.
    """

    def test_waffle_switch_namespace_override(self):
        namespace = WaffleSwitchNamespace("namespace")
        with namespace.override("waffle_switch1", True):
            self.assertTrue(namespace.is_enabled("waffle_switch1"))
