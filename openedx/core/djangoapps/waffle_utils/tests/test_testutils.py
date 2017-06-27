"""
Tests for waffle utils test utilities.
"""
from django.test import TestCase
from opaque_keys.edx.keys import CourseKey

from request_cache.middleware import RequestCache

from .. import CourseWaffleFlag, WaffleFlagNamespace
from ..testutils import override_waffle_flag


class OverrideWaffleFlagTests(TestCase):
    """
    Tests for the override_waffle_flag decorator.
    """

    NAMESPACE_NAME = "test_namespace"
    FLAG_NAME = "test_flag"
    NAMESPACED_FLAG_NAME = NAMESPACE_NAME + "." + FLAG_NAME

    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    TEST_NAMESPACE = WaffleFlagNamespace(NAMESPACE_NAME)
    TEST_COURSE_FLAG = CourseWaffleFlag(TEST_NAMESPACE, FLAG_NAME)

    def setUp(self):
        super(OverrideWaffleFlagTests, self).setUp()
        RequestCache.clear_request_cache()

    @override_waffle_flag(TEST_COURSE_FLAG, True)
    def check_is_enabled_with_decorator(self):
        # test flag while overridden with decorator
        self.assertTrue(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY))

    def test_override_waffle_flag_pre_cached(self):
        # checks and caches the is_enabled value
        self.assertFalse(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY))
        flag_cache = self.TEST_COURSE_FLAG.waffle_namespace._cached_flags
        self.assertIn(self.NAMESPACED_FLAG_NAME, flag_cache)

        # test flag while overridden with decorator
        self.check_is_enabled_with_decorator()

        # test cached flag is restored
        self.assertIn(self.NAMESPACED_FLAG_NAME, flag_cache)
        self.assertEquals(self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY), False)

    def test_override_waffle_flag_not_pre_cached(self):
        # check that the flag is not yet cached
        flag_cache = self.TEST_COURSE_FLAG.waffle_namespace._cached_flags
        self.assertNotIn(self.NAMESPACED_FLAG_NAME, flag_cache)

        # test flag while overridden with decorator
        self.check_is_enabled_with_decorator()

        # test cache is removed when no longer using decorator/context manager
        self.assertNotIn(self.NAMESPACED_FLAG_NAME, flag_cache)
