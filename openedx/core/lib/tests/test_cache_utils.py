# -*- coding: utf-8 -*-
"""
Tests for cache_utils.py
"""

from unittest import TestCase

import ddt
import six
from edx_django_utils.cache import RequestCache
from mock import Mock

from openedx.core.lib.cache_utils import request_cached


@ddt.ddt
class TestRequestCachedDecorator(TestCase):
    """
    Test the request_cached decorator.
    """
    def setUp(self):
        RequestCache.clear_all_namespaces()

    def test_request_cached_miss_and_then_hit(self):
        """
        Ensure that after a cache miss, we fill the cache and can hit it.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.return_value = 42
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        wrapped = request_cached()(mock_wrapper)
        result = wrapped()
        self.assertEqual(result, 42)
        self.assertEqual(to_be_wrapped.call_count, 1)

        result = wrapped()
        self.assertEqual(result, 42)
        self.assertEqual(to_be_wrapped.call_count, 1)

    def test_request_cached_with_caches_despite_changing_wrapped_result(self):
        """
        Ensure that after caching a result, we always send it back, even if the underlying result changes.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [1, 2, 3]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        wrapped = request_cached()(mock_wrapper)
        result = wrapped()
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        result = wrapped()
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        direct_result = mock_wrapper()
        self.assertEqual(direct_result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)

        result = wrapped()
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 2)

        direct_result = mock_wrapper()
        self.assertEqual(direct_result, 3)
        self.assertEqual(to_be_wrapped.call_count, 3)

    def test_request_cached_with_changing_args(self):
        """
        Ensure that calling a decorated function with different positional arguments
        will not use a cached value invoked by a previous call with different arguments.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [1, 2, 3, 4, 5, 6]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        wrapped = request_cached()(mock_wrapper)

        # This will be a miss, and make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        # This will be a miss, and make an underlying call.
        result = wrapped(2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # This is bypass of the decorator.
        direct_result = mock_wrapper(3)
        self.assertEqual(direct_result, 3)
        self.assertEqual(to_be_wrapped.call_count, 3)

        # These will be hits, and not make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 3)

        result = wrapped(2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 3)

    def test_request_cached_with_changing_kwargs(self):
        """
        Ensure that calling a decorated function with different keyword arguments
        will not use a cached value invoked by a previous call with different arguments.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [1, 2, 3, 4, 5, 6]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        wrapped = request_cached()(mock_wrapper)

        # This will be a miss, and make an underlying call.
        result = wrapped(1, foo=1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        # This will be a miss, and make an underlying call.
        result = wrapped(2, foo=2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # This is bypass of the decorator.
        direct_result = mock_wrapper(3, foo=3)
        self.assertEqual(direct_result, 3)
        self.assertEqual(to_be_wrapped.call_count, 3)

        # These will be hits, and not make an underlying call.
        result = wrapped(1, foo=1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 3)

        result = wrapped(2, foo=2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 3)

        # Since we're changing foo, this will be a miss.
        result = wrapped(2, foo=5)
        self.assertEqual(result, 4)
        self.assertEqual(to_be_wrapped.call_count, 4)

        # Since we're adding bar, this will be a miss.
        result = wrapped(2, foo=1, bar=2)
        self.assertEqual(result, 5)
        self.assertEqual(to_be_wrapped.call_count, 5)

        # Should be a hit, even when kwargs are in a different order
        result = wrapped(2, bar=2, foo=1)
        self.assertEqual(result, 5)
        self.assertEqual(to_be_wrapped.call_count, 5)

    def test_request_cached_mixed_unicode_str_args(self):
        """
        Ensure that request_cached can work with mixed str and Unicode parameters.
        """
        def dummy_function(arg1, arg2):
            """
            A dummy function that expects an str and unicode arguments.
            """
            assert isinstance(arg1, str), 'First parameter has to be of type `str`'
            assert isinstance(arg2, six.text_type), 'Second parameter has to be of type `unicode`'
            return True

        self.assertTrue(dummy_function('Hello', u'World'), 'Should be callable with ASCII chars')
        self.assertTrue(dummy_function('H∂llå', u'Wørld'), 'Should be callable with non-ASCII chars')

        wrapped = request_cached()(dummy_function)

        self.assertTrue(wrapped('Hello', u'World'), 'Wrapper should handle ASCII only chars')
        self.assertTrue(wrapped('H∂llå', u'Wørld'), 'Wrapper should handle non-ASCII chars')

    def test_request_cached_with_none_result(self):
        """
        Ensure that calling a decorated function that returns None
        properly caches the result and doesn't recall the underlying
        function.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [None, None, None, 1, 1]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        wrapped = request_cached()(mock_wrapper)

        # This will be a miss, and make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, None)
        self.assertEqual(to_be_wrapped.call_count, 1)

        # This will be a miss, and make an underlying call.
        result = wrapped(2)
        self.assertEqual(result, None)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # This is bypass of the decorator.
        direct_result = mock_wrapper(3)
        self.assertEqual(direct_result, None)
        self.assertEqual(to_be_wrapped.call_count, 3)

        # These will be hits, and not make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, None)
        self.assertEqual(to_be_wrapped.call_count, 3)

        result = wrapped(2)
        self.assertEqual(result, None)
        self.assertEqual(to_be_wrapped.call_count, 3)

    def test_request_cached_with_request_cache_getter(self):
        """
        Ensure that calling a decorated function uses
        request_cache_getter if supplied.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [1, 2, 3]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        request_cache_getter = lambda args, kwargs: RequestCache('test')
        wrapped = request_cached(request_cache_getter=request_cache_getter)(mock_wrapper)

        # This will be a miss, and make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        # This will be a miss, and make an underlying call.
        result = wrapped(2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # These will be a hits, and not make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # Ensure the appropriate request cache was used
        self.assertFalse(RequestCache().data)
        self.assertTrue(RequestCache('test').data)

    def test_request_cached_with_arg_map_function(self):
        """
        Ensure that calling a decorated function uses
        arg_map_function to determined the cache key.
        """
        to_be_wrapped = Mock()
        to_be_wrapped.side_effect = [1, 2, 3]
        self.assertEqual(to_be_wrapped.call_count, 0)

        def mock_wrapper(*args, **kwargs):
            """Simple wrapper to let us decorate our mock."""
            return to_be_wrapped(*args, **kwargs)

        arg_map_function = lambda arg: six.text_type(arg == 1)
        wrapped = request_cached(arg_map_function=arg_map_function)(mock_wrapper)

        # This will be a miss, and make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 1)

        # This will be a miss, and make an underlying call.
        result = wrapped(2)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)

        # These will be a hits, and not make an underlying call.
        result = wrapped(1)
        self.assertEqual(result, 1)
        self.assertEqual(to_be_wrapped.call_count, 2)

        result = wrapped(3)
        self.assertEqual(result, 2)
        self.assertEqual(to_be_wrapped.call_count, 2)
