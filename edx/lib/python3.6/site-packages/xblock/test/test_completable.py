"""
Tests of the CompletableXBlockMixin.
"""
from __future__ import absolute_import, unicode_literals

import math
from collections import namedtuple
from unittest import TestCase

import ddt
import mock
from hypothesis import given, example
import hypothesis.strategies as strategies

from xblock.core import XBlock
from xblock.fields import ScopeIds
from xblock.runtime import Runtime
from xblock.completable import CompletableXBlockMixin, XBlockCompletionMode


@ddt.ddt
class XBlockCompletionModeTest(TestCase):
    """
    Tests for XBlockCompletionMode
    """
    blocklike = namedtuple('block_like', ['completion_mode'])

    @ddt.data(
        XBlockCompletionMode.COMPLETABLE,
        XBlockCompletionMode.AGGREGATOR,
        XBlockCompletionMode.EXCLUDED,
    )
    def test_explicit_mode(self, mode):
        block = self.blocklike(mode)
        self.assertEqual(
            XBlockCompletionMode.get_mode(block),
            mode
        )

    def test_no_mode(self):
        self.assertEqual(
            XBlockCompletionMode.get_mode(object()),
            XBlockCompletionMode.COMPLETABLE,
        )

    def test_unknown_mode(self):
        block = self.blocklike('somenewmode')
        self.assertEqual(
            XBlockCompletionMode.get_mode(block),
            'somenewmode'
        )


class CompletableXBlockMixinTest(TestCase):
    """
    Tests for CompletableXBlockMixin.
    """
    class TestBuddyXBlock(XBlock, CompletableXBlockMixin):
        """
        Simple XBlock extending CompletableXBlockMixin.
        """

    class TestIllegalCustomCompletionAttrXBlock(XBlock, CompletableXBlockMixin):
        """
        XBlock extending CompletableXBlockMixin using illegal `has_custom_completion` attribute.
        """
        has_custom_completion = False

    class TestIllegalCompletionMethodAttrXBlock(XBlock, CompletableXBlockMixin):
        """
        XBlock extending CompletableXBlockMixin using illegal `completion_mode` attribute.
        """
        completion_mode = "something_else"

    def _make_block(self, runtime=None, block_type=None):
        """
        Creates a test block.
        """
        block_type = block_type if block_type else self.TestBuddyXBlock
        runtime = runtime if runtime else mock.Mock(spec=Runtime)
        scope_ids = ScopeIds("user_id", "test_buddy", "def_id", "usage_id")
        return block_type(runtime=runtime, scope_ids=scope_ids)

    def test_has_custom_completion_property(self):
        """
        Test `has_custom_completion` property is set by mixin.
        """
        block = self._make_block()
        self.assertTrue(block.has_custom_completion)
        self.assertTrue(getattr(block, 'has_custom_completion', False))

    def test_completion_mode_property(self):
        """
        Test `completion_mode` property is set by mixin.
        """
        block = self._make_block()
        self.assertEqual(XBlockCompletionMode.get_mode(block), XBlockCompletionMode.COMPLETABLE)
        self.assertEqual(getattr(block, 'completion_mode'), XBlockCompletionMode.COMPLETABLE)

    @given(strategies.floats())
    def test_emit_completion_illegal_custom_completion(self, any_completion):
        """
        Test `emit_completion` raises exception when called on a XBlock with illegal `has_custom_completion` value.
        """
        runtime_mock = mock.Mock(spec=Runtime)
        illegal_custom_completion_block = self._make_block(runtime_mock, self.TestIllegalCustomCompletionAttrXBlock)
        with self.assertRaises(AttributeError):
            illegal_custom_completion_block.emit_completion(any_completion)

    @given(strategies.floats())
    def test_emit_completion_completion_mode(self, any_completion):
        """
        Test `emit_completion` raises exception when called on a XBlock with illegal `completion_mode` value.
        """
        runtime_mock = mock.Mock(spec=Runtime)
        illegal_completion_mode_block = self._make_block(runtime_mock, self.TestIllegalCompletionMethodAttrXBlock)
        with self.assertRaises(AttributeError):
            illegal_completion_mode_block.emit_completion(any_completion)

    @given(strategies.floats(min_value=0.0, max_value=1.0))
    @example(1.0)
    @example(0.0)
    def test_emit_completion_emits_event(self, valid_completion_percent):
        """
        Test `emit_completion` emits completion events when passed a valid argument.

        Given a valid completion percent
        When emit_completion is called
        Then runtime.publish is called with expected arguments
        """
        runtime_mock = mock.Mock(spec=Runtime)
        block = self._make_block(runtime_mock)
        block.emit_completion(valid_completion_percent)

        runtime_mock.publish.assert_called_once_with(block, "completion", {"completion": valid_completion_percent})

    @given(strategies.floats().filter(lambda x: math.isnan(x) or x < 0.0 or x > 1.0))
    @example(None)
    @example(float('+inf'))
    @example(float('-inf'))
    def test_emit_completion_raises_assertion_error_if_invalid(self, invalid_completion_percent):
        """
        Test `emit_completion` raises exception when passed an invalid argument.

        Given an invalid completion percent
            * Less than 0.0
            * Greater than 1.0
            * Positive or negative infinity
            * NaN
        When emit_completion is called
        Then value error is thrown
        """
        runtime_mock = mock.Mock(spec=Runtime)
        block = self._make_block(runtime_mock)
        with self.assertRaises(ValueError):
            self.assertRaises(block.emit_completion(invalid_completion_percent))
