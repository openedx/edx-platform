"""
Tests of the utility FieldData's defined by xblock
"""

from __future__ import absolute_import, division, print_function, unicode_literals

from mock import Mock
import pytest

from xblock.core import XBlock
from xblock.exceptions import InvalidScopeError
from xblock.fields import Scope, String
from xblock.field_data import SplitFieldData, ReadOnlyFieldData
from xblock.test.tools import TestRuntime


class TestingBlock(XBlock):
    """
    An XBlock for use in the tests below.

    It has fields in a handful of scopes to test that the different scopes
    do the right thing with a split fielddata.

    """
    __test__ = False
    content = String(scope=Scope.content)
    settings = String(scope=Scope.settings)
    user_state = String(scope=Scope.user_state)


class TestSplitFieldData(object):
    """
    Tests of :ref:`SplitFieldData`.
    """
    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """
        Setup for each test case in this class.
        """
        self.content = Mock()
        self.settings = Mock()
        self.split = SplitFieldData({
            Scope.content: self.content,
            Scope.settings: self.settings
        })
        self.runtime = TestRuntime(services={'field-data': self.split})
        self.block = TestingBlock(
            runtime=self.runtime,
            scope_ids=Mock(),
        )
    # pylint: enable=attribute-defined-outside-init

    def test_get(self):
        self.split.get(self.block, 'content')
        self.content.get.assert_called_once_with(self.block, 'content')
        assert not self.settings.get.called

    def test_set(self):
        self.split.set(self.block, 'content', 'foo')
        self.content.set.assert_called_once_with(self.block, 'content', 'foo')
        assert not self.settings.set.called

    def test_delete(self):
        self.split.delete(self.block, 'content')
        self.content.delete.assert_called_once_with(self.block, 'content')
        assert not self.settings.delete.called

    def test_has(self):
        self.split.has(self.block, 'content')
        self.content.has.assert_called_once_with(self.block, 'content')
        assert not self.settings.has.called

    def test_set_many(self):
        self.split.set_many(self.block, {'content': 'new content', 'settings': 'new settings'})
        self.content.set_many.assert_called_once_with(self.block, {'content': 'new content'})
        self.settings.set_many.assert_called_once_with(self.block, {'settings': 'new settings'})

    def test_invalid_scope(self):
        with pytest.raises(InvalidScopeError):
            self.split.get(self.block, 'user_state')

    def test_default(self):
        self.split.default(self.block, 'content')
        self.content.default.assert_called_once_with(self.block, 'content')
        assert not self.settings.default.called


class TestReadOnlyFieldData(object):
    """
    Tests of :ref:`ReadOnlyFieldData`.
    """
    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """
        Setup for each test case in this class.
        """
        self.source = Mock()
        self.read_only = ReadOnlyFieldData(self.source)
        self.runtime = TestRuntime(services={'field-data': self.read_only})
        self.block = TestingBlock(
            runtime=self.runtime,
            scope_ids=Mock(),
        )
    # pylint: enable=attribute-defined-outside-init

    def test_get(self):
        assert self.source.get.return_value == self.read_only.get(self.block, 'content')
        self.source.get.assert_called_once_with(self.block, 'content')

    def test_set(self):
        with pytest.raises(InvalidScopeError):
            self.read_only.set(self.block, 'content', 'foo')

    def test_delete(self):
        with pytest.raises(InvalidScopeError):
            self.read_only.delete(self.block, 'content')

    def test_set_many(self):
        with pytest.raises(InvalidScopeError):
            self.read_only.set_many(self.block, {'content': 'foo', 'settings': 'bar'})

    def test_default(self):
        assert self.source.default.return_value == self.read_only.default(self.block, 'content')
        self.source.default.assert_called_once_with(self.block, 'content')

    def test_has(self):
        assert self.source.has.return_value == self.read_only.has(self.block, 'content')
        self.source.has.assert_called_once_with(self.block, 'content')
