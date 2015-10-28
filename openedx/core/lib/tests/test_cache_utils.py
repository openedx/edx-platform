"""
Tests for cache_utils.py
"""
import ddt
from mock import MagicMock
from unittest import TestCase

from openedx.core.lib.cache_utils import memoize_in_request_cache


@ddt.ddt
class TestMemoizeInRequestCache(TestCase):
    """
    Test the memoize_in_request_cache helper function.
    """
    class TestCache(object):
        """
        A test cache that provides a data dict for caching values, analogous to the request_cache.
        """
        def __init__(self):
            self.data = {}

    def setUp(self):
        super(TestMemoizeInRequestCache, self).setUp()
        self.request_cache = self.TestCache()

    @memoize_in_request_cache('request_cache')
    def func_to_memoize(self, param):
        """
        A test function whose results are to be memoized in the request_cache.
        """
        return self.func_to_count(param)

    @memoize_in_request_cache('request_cache')
    def multi_param_func_to_memoize(self, param1, param2):
        """
        A test function with multiple parameters whose results are to be memoized in the request_cache.
        """
        return self.func_to_count(param1, param2)

    def test_memoize_in_request_cache(self):
        """
        Tests the memoize_in_request_cache decorator for both single-param and multiple-param functions.
        """
        funcs_to_test = (
            (self.func_to_memoize, ['foo'], ['bar']),
            (self.multi_param_func_to_memoize, ['foo', 'foo2'], ['foo', 'foo3']),
        )

        for func_to_memoize, arg_list1, arg_list2 in funcs_to_test:
            self.func_to_count = MagicMock()  # pylint: disable=attribute-defined-outside-init
            self.assertFalse(self.func_to_count.called)

            func_to_memoize(*arg_list1)
            self.func_to_count.assert_called_once_with(*arg_list1)

            func_to_memoize(*arg_list1)
            self.func_to_count.assert_called_once_with(*arg_list1)

            for _ in range(10):
                func_to_memoize(*arg_list1)
                func_to_memoize(*arg_list2)

            self.assertEquals(self.func_to_count.call_count, 2)
