"""
Tests for waffle utils test utilities.
"""

import crum
from django.test import TestCase
from django.test.client import RequestFactory
from edx_django_utils.cache import RequestCache
from opaque_keys.edx.keys import CourseKey

from .. import CourseWaffleFlag, WaffleFlagNamespace
from ..testutils import override_waffle_flag


class OverrideWaffleFlagTests(TestCase):
    """
    Tests for the override_waffle_flag decorator/context manager.
    """

    NAMESPACE_NAME = "test_namespace"
    FLAG_NAME = "test_flag"
    NAMESPACED_FLAG_NAME = NAMESPACE_NAME + "." + FLAG_NAME

    TEST_COURSE_KEY = CourseKey.from_string("edX/DemoX/Demo_Course")
    TEST_NAMESPACE = WaffleFlagNamespace(NAMESPACE_NAME)
    TEST_COURSE_FLAG = CourseWaffleFlag(TEST_NAMESPACE, FLAG_NAME)

    def setUp(self):
        super(OverrideWaffleFlagTests, self).setUp()
        request = RequestFactory().request()
        self.addCleanup(crum.set_current_request, None)
        crum.set_current_request(request)
        RequestCache.clear_all_namespaces()

    @override_waffle_flag(TEST_COURSE_FLAG, True)
    def assert_decorator_activates_flag(self):
        assert self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)

    def test_override_waffle_flag_pre_cached(self):
        # checks and caches the is_enabled value
        assert not self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)
        flag_cache = self.TEST_COURSE_FLAG.waffle_namespace._cached_flags
        assert self.NAMESPACED_FLAG_NAME in flag_cache

        self.assert_decorator_activates_flag()

        # test cached flag is restored
        assert self.NAMESPACED_FLAG_NAME in flag_cache
        assert not self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)

    def test_override_waffle_flag_not_pre_cached(self):
        # check that the flag is not yet cached
        flag_cache = self.TEST_COURSE_FLAG.waffle_namespace._cached_flags
        assert self.NAMESPACED_FLAG_NAME not in flag_cache

        self.assert_decorator_activates_flag()

        # test cache is removed when no longer using decorator/context manager
        assert self.NAMESPACED_FLAG_NAME not in flag_cache

    def test_override_waffle_flag_as_context_manager(self):
        assert not self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)

        with override_waffle_flag(self.TEST_COURSE_FLAG, True):
            assert self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)

        assert not self.TEST_COURSE_FLAG.is_enabled(self.TEST_COURSE_KEY)
