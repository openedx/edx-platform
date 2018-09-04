"""
Tests for waffle utils features.
"""
import crum
import ddt
from django.test import TestCase
from django.test.client import RequestFactory
from edx_django_utils.cache import RequestCache
from mock import patch
from opaque_keys.edx.keys import CourseKey
from waffle.testutils import override_flag

from .. import CourseWaffleFlag, WaffleFlagNamespace, WaffleSwitchNamespace, WaffleSwitch
from ..models import WaffleFlagCourseOverrideModel


@ddt.ddt
class TestCourseWaffleFlag(TestCase):
    """
    Tests the CourseWaffleFlag.
    """

    NAMESPACE_NAME = "test_namespace"
    FLAG_NAME = "test_flag"
    NAMESPACED_FLAG_NAME = NAMESPACE_NAME + "." + FLAG_NAME

    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    TEST_COURSE_2_KEY = CourseKey.from_string("edX/DemoX/Demo_Course_2")
    TEST_NAMESPACE = WaffleFlagNamespace(NAMESPACE_NAME)
    TEST_COURSE_FLAG = CourseWaffleFlag(TEST_NAMESPACE, FLAG_NAME)

    def setUp(self):
        super(TestCourseWaffleFlag, self).setUp()
        request = RequestFactory().request()
        self.addCleanup(crum.set_current_request, None)
        crum.set_current_request(request)
        RequestCache.clear_all_namespaces()

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
                WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                    self.NAMESPACED_FLAG_NAME,
                    self.TEST_COURSE_KEY
                )

        # check flag for a second course
        if data['course_override'] == WaffleFlagCourseOverrideModel.ALL_CHOICES.unset:
            # When course override wasn't set for the first course, the second course will get the same
            # cached value from waffle.
            self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), data['waffle_enabled'])
        else:
            # When course override was set for the first course, it should not apply to the second
            # course which should get the default value of False.
            self.assertEqual(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_2_KEY), False)

    @ddt.data(
        {'flag_undefined_default': None, 'result': False},
        {'flag_undefined_default': False, 'result': False},
        {'flag_undefined_default': True, 'result': True},
    )
    def test_undefined_waffle_flag(self, data):
        """
        Test flag with various defaults provided for undefined waffle flags.
        """
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            flag_undefined_default=data['flag_undefined_default']
        )

        with patch.object(
            WaffleFlagCourseOverrideModel,
            'override_value',
            return_value=WaffleFlagCourseOverrideModel.ALL_CHOICES.unset
        ):
            # check twice to test that the result is properly cached
            self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])
            self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])
            # result is cached, so override check should happen once
            WaffleFlagCourseOverrideModel.override_value.assert_called_once_with(
                self.NAMESPACED_FLAG_NAME,
                self.TEST_COURSE_KEY
            )

    @ddt.data(
        {'flag_undefined_default': None, 'result': False},
        {'flag_undefined_default': False, 'result': False},
        {'flag_undefined_default': True, 'result': True},
    )
    def test_without_request(self, data):
        """
        Test the flag behavior when outside a request context.
        """
        crum.set_current_request(None)
        test_course_flag = CourseWaffleFlag(
            self.TEST_NAMESPACE,
            self.FLAG_NAME,
            flag_undefined_default=data['flag_undefined_default']
        )
        self.assertEqual(test_course_flag.is_enabled(self.TEST_COURSE_KEY), data['result'])


class TestWaffleSwitch(TestCase):
    """
    Tests the WaffleSwitch.
    """

    NAMESPACE_NAME = "test_namespace"
    WAFFLE_SWITCH_NAME = "test_switch_name"
    TEST_NAMESPACE = WaffleSwitchNamespace(NAMESPACE_NAME)
    WAFFLE_SWITCH = WaffleSwitch(TEST_NAMESPACE, WAFFLE_SWITCH_NAME)

    def test_namespaced_switch_name(self):
        """
        Verify namespaced_switch_name returns the correct namespace switch name
        """
        expected = self.NAMESPACE_NAME + "." + self.WAFFLE_SWITCH_NAME
        actual = self.WAFFLE_SWITCH.namespaced_switch_name
        self.assertEqual(actual, expected)
