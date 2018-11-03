# -*- coding: utf-8 -*-
"""
Tests the fundamentals of XBlocks including - but not limited to -
metaclassing, field access, caching, serialization, and bulk saves.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

# Allow accessing protected members for testing purposes
# pylint: disable=protected-access
from datetime import datetime
import json
import re
import unittest

import ddt
import six
from mock import patch, MagicMock, Mock
import pytest
from webob import Response

from xblock.core import XBlock
from xblock.exceptions import (
    XBlockSaveError,
    KeyValueMultiSaveError,
    JsonHandlerError,
    DisallowedFileError,
    FieldDataDeprecationWarning,
)
from xblock.fields import Dict, Float, Integer, List, Set, Field, Scope, ScopeIds
from xblock.field_data import FieldData, DictFieldData
from xblock.mixins import ScopedStorageMixin
from xblock.runtime import Runtime

from xblock.test.tools import (
    WarningTestMixin,
    TestRuntime,
)


def test_field_access():
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default=42)
        float_a = Float(scope=Scope.settings, default=5.8)
        float_b = Float(scope=Scope.settings)

    field_data = DictFieldData({'field_a': 5, 'float_a': 6.1, 'field_x': 15})

    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock())
    # Verify that the fields have been set
    assert field_tester.field_a == 5
    assert field_tester.field_b == 10
    assert field_tester.field_c == 42
    assert field_tester.float_a == 6.1
    assert field_tester.float_b is None
    assert not hasattr(field_tester, 'field_x')

    # Set two of the fields.
    field_tester.field_a = 20
    field_tester.float_a = 20.5
    # field_a should be updated in the cache, but /not/ in the underlying db.
    assert field_tester.field_a == 20
    assert field_tester.float_a == 20.5
    assert field_data.get(field_tester, 'field_a') == 5
    assert field_data.get(field_tester, 'float_a') == 6.1
    # save the XBlock
    field_tester.save()
    # verify that the fields have been updated correctly
    assert field_tester.field_a == 20
    assert field_tester.float_a == 20.5
    # Now, field_a should be updated in the underlying db
    assert field_data.get(field_tester, 'field_a') == 20
    assert field_data.get(field_tester, 'float_a') == 20.5
    assert field_tester.field_b == 10
    assert field_tester.field_c == 42
    assert field_tester.float_b is None

    # Deletes happen immediately (do not require a save)
    del field_tester.field_a
    del field_tester.float_a

    # After delete, we should find default values in the cache
    assert field_tester.field_a is None
    assert field_tester.float_a == 5.8
    # But the fields should not actually be present in the underlying kvstore
    with pytest.raises(KeyError):
        field_data.get(field_tester, 'field_a')
    assert not field_data.has(field_tester, 'field_a')
    with pytest.raises(KeyError):
        field_data.get(field_tester, 'float_a')
    assert not field_data.has(field_tester, 'float_a')


def test_list_field_access():
    # Check that lists are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.content, default=[1, 2, 3])
        field_c = List(scope=Scope.content, default=[4, 5, 6])
        field_d = List(scope=Scope.settings)

    field_data = DictFieldData({'field_a': [200], 'field_b': [11, 12, 13]})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

    # Check initial values have been set properly
    assert [200] == field_tester.field_a
    assert [11, 12, 13] == field_tester.field_b
    assert [4, 5, 6] == field_tester.field_c
    assert [] == field_tester.field_d

    # Update the fields
    field_tester.field_a.append(1)
    field_tester.field_b.append(14)
    field_tester.field_c.append(7)
    field_tester.field_d.append(1)

    # The fields should be update in the cache, but /not/ in the underlying kvstore.
    assert [200, 1] == field_tester.field_a
    assert [11, 12, 13, 14] == field_tester.field_b
    assert [4, 5, 6, 7] == field_tester.field_c
    assert [1] == field_tester.field_d

    # Examine model data directly
    #  Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    #  when we instantiate the XBlock. So, the values for those two in both `field_data` and `_field_data_cache`
    #  point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    #  `field_data` right now. `field_c` does not, because it has never been written to the `field_data`.
    assert not field_data.has(field_tester, 'field_c')
    assert not field_data.has(field_tester, 'field_d')

    # save the XBlock
    field_tester.save()

    # verify that the fields have been updated correctly
    assert [200, 1] == field_tester.field_a
    assert [11, 12, 13, 14] == field_tester.field_b
    assert [4, 5, 6, 7] == field_tester.field_c
    assert [1] == field_tester.field_d
    # Now, the fields should be updated in the underlying kvstore

    assert [200, 1] == field_data.get(field_tester, 'field_a')
    assert [11, 12, 13, 14] == field_data.get(field_tester, 'field_b')
    assert [4, 5, 6, 7] == field_data.get(field_tester, 'field_c')
    assert [1] == field_data.get(field_tester, 'field_d')


def test_set_field_access():
    # Check that sets are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Set(scope=Scope.settings)
        field_b = Set(scope=Scope.content, default=[1, 2, 3])
        field_c = Set(scope=Scope.content, default=[4, 5, 6])
        field_d = Set(scope=Scope.settings)

    field_tester = FieldTester(MagicMock(), DictFieldData({'field_a': [200], 'field_b': [11, 12, 13]}), Mock())

    # Check initial values have been set properly
    assert set([200]) == field_tester.field_a
    assert set([11, 12, 13]) == field_tester.field_b
    assert set([4, 5, 6]) == field_tester.field_c
    assert set() == field_tester.field_d

    # Update the fields
    field_tester.field_a.add(1)
    field_tester.field_b.add(14)
    field_tester.field_c.remove(5)
    field_tester.field_d.add(1)

    # The fields should be update in the cache, but /not/ in the underlying kvstore.
    assert set([200, 1]) == field_tester.field_a
    assert set([11, 12, 13, 14]) == field_tester.field_b
    assert set([4, 6]) == field_tester.field_c
    assert set([1]) == field_tester.field_d

    # Examine model data directly
    #  Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    #  when we instantiate the XBlock. So, the values for those two in both `_field_data` and `_field_data_cache`
    #  point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    #  `_field_data` right now. `field_c` does not, because it has never been written to the `_field_data`.
    assert not field_tester._field_data.has(field_tester, 'field_c')
    assert not field_tester._field_data.has(field_tester, 'field_d')

    # save the XBlock
    field_tester.save()

    # verify that the fields have been updated correctly
    assert set([200, 1]) == field_tester.field_a
    assert set([11, 12, 13, 14]) == field_tester.field_b
    assert set([4, 6]) == field_tester.field_c
    assert set([1]) == field_tester.field_d
    # Now, the fields should be updated in the underlying kvstore

    assert set([200, 1]) == field_tester._field_data.get(field_tester, 'field_a')
    assert set([11, 12, 13, 14]) == field_tester._field_data.get(field_tester, 'field_b')
    assert set([4, 6]) == field_tester._field_data.get(field_tester, 'field_c')
    assert set([1]) == field_tester._field_data.get(field_tester, 'field_d')


def test_mutable_none_values():
    # Check that fields with values intentionally set to None
    # save properly.
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = List(scope=Scope.settings)
        field_b = List(scope=Scope.settings)
        field_c = List(scope=Scope.content, default=None)

    field_tester = FieldTester(
        TestRuntime(services={'field-data': DictFieldData({'field_a': None})}),
        scope_ids=Mock(spec=ScopeIds)
    )
    # Set fields b & c to None
    field_tester.field_b = None
    field_tester.field_c = None
    # Save our changes
    field_tester.save()

    # Access the fields without modifying them. Want to call `__get__`, not `__set__`,
    # because `__get__` marks only mutable fields as dirty.
    _test_get = field_tester.field_a
    _test_get = field_tester.field_b
    _test_get = field_tester.field_c

    # The previous accesses will mark the fields as dirty (via __get__)
    assert len(field_tester._dirty_fields) == 3  # pylint: disable=W0212

    # However, the fields should not ACTUALLY be marked as fields that need to be saved.
    assert len(field_tester._get_fields_to_save()) == 0  # pylint: disable=W0212


def test_dict_field_access():
    # Check that dicts are correctly saved when not directly set
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        field_a = Dict(scope=Scope.settings)
        field_b = Dict(scope=Scope.content, default={'a': 1, 'b': 2, 'c': 3})
        field_c = Dict(scope=Scope.content, default={'a': 4, 'b': 5, 'c': 6})
        field_d = Dict(scope=Scope.settings)

    field_data = DictFieldData({
        'field_a': {'a': 200},
        'field_b': {'a': 11, 'b': 12, 'c': 13}
    })

    field_tester = FieldTester(
        TestRuntime(services={'field-data': field_data}),
        None,
        Mock()
    )

    # Check initial values have been set properly
    assert {'a': 200} == field_tester.field_a
    assert {'a': 11, 'b': 12, 'c': 13} == field_tester.field_b
    assert {'a': 4, 'b': 5, 'c': 6} == field_tester.field_c
    assert {} == field_tester.field_d

    # Update the fields
    field_tester.field_a['a'] = 250
    field_tester.field_b['d'] = 14
    field_tester.field_c['a'] = 0
    field_tester.field_d['new'] = 'value'

    # The fields should be update in the cache, but /not/ in the underlying kvstore.
    assert {'a': 250} == field_tester.field_a
    assert {'a': 11, 'b': 12, 'c': 13, 'd': 14} == field_tester.field_b
    assert {'a': 0, 'b': 5, 'c': 6} == field_tester.field_c
    assert {'new': 'value'} == field_tester.field_d

    # Examine model data directly
    #  Caveat: there's not a clean way to copy the originally provided values for `field_a` and `field_b`
    #  when we instantiate the XBlock. So, the values for those two in both `field_data` and `_field_data_cache`
    #  point at the same object. Thus, `field_a` and `field_b` actually have the correct values in
    #  `field_data` right now. `field_c` does not, because it has never been written to the `field_data`.
    assert not field_data.has(field_tester, 'field_c')
    assert not field_data.has(field_tester, 'field_d')

    field_tester.save()
    # verify that the fields have been updated correctly
    assert {'a': 250} == field_tester.field_a
    assert {'a': 11, 'b': 12, 'c': 13, 'd': 14} == field_tester.field_b
    assert {'a': 0, 'b': 5, 'c': 6} == field_tester.field_c
    assert {'new': 'value'} == field_tester.field_d

    # Now, the fields should be updated in the underlying kvstore
    assert {'a': 250} == field_data.get(field_tester, 'field_a')
    assert {'a': 11, 'b': 12, 'c': 13, 'd': 14} == field_data.get(field_tester, 'field_b')
    assert {'a': 0, 'b': 5, 'c': 6} == field_data.get(field_tester, 'field_c')
    assert {'new': 'value'} == field_data.get(field_tester, 'field_d')


def test_default_values():
    # Check that values that are deleted are restored to their default values
    class FieldTester(XBlock):
        """Test XBlock for field access testing"""
        dic1 = Dict(scope=Scope.settings)
        dic2 = Dict(scope=Scope.content, default={'a': 1, 'b': 2, 'c': 3})
        list1 = List(scope=Scope.settings)
        list2 = List(scope=Scope.content, default=[1, 2, 3])

    field_data = DictFieldData({'dic1': {'a': 200}, 'list1': ['a', 'b']})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

    assert {'a': 200} == field_tester.dic1
    assert {'a': 1, 'b': 2, 'c': 3} == field_tester.dic2
    assert ['a', 'b'] == field_tester.list1
    assert [1, 2, 3] == field_tester.list2
    # Modify the fields & save
    field_tester.dic1.popitem()
    field_tester.dic2.clear()
    field_tester.list1.pop()
    field_tester.list2.remove(2)
    field_tester.save()

    # Test that after save, new values exist and fields are present in the underlying kvstore
    assert {} == field_tester.dic1
    assert {} == field_tester.dic2
    assert ['a'] == field_tester.list1
    assert [1, 3] == field_tester.list2
    for fname in ['dic1', 'dic2', 'list1', 'list2']:
        assert field_data.has(field_tester, fname)

    # Now delete each field
    del field_tester.dic1
    del field_tester.dic2
    del field_tester.list1
    del field_tester.list2

    # Test that default values return after a delete, but fields not actually
    # in the underlying kvstore

    # Defaults not explicitly set
    assert {} == field_tester.dic1
    assert [] == field_tester.list1
    # Defaults explicitly set
    assert {'a': 1, 'b': 2, 'c': 3} == field_tester.dic2
    assert [1, 2, 3] == field_tester.list2
    for fname in ['dic1', 'dic2', 'list1', 'list2']:
        assert not field_data.has(field_tester, fname)


def test_json_field_access():
    # Check that values are correctly converted to and from json in accessors.

    class Date(Field):
        """Date needs to convert between JSON-compatible persistence and a datetime object"""
        def from_json(self, field):
            """Convert a string representation of a date to a datetime object"""
            return datetime.strptime(field, "%m/%d/%Y")

        def to_json(self, value):
            """Convert a datetime object to a string"""
            return value.strftime("%m/%d/%Y")

    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""

        field_a = Date(scope=Scope.settings)
        field_b = Date(scope=Scope.content, default=datetime(2013, 4, 1))

    field_tester = FieldTester(
        runtime=TestRuntime(services={'field-data': DictFieldData({})}),
        scope_ids=MagicMock(spec=ScopeIds)
    )

    # Check initial values
    assert field_tester.field_a is None
    assert datetime(2013, 4, 1) == field_tester.field_b

    # Test no default specified
    field_tester.field_a = datetime(2013, 1, 2)
    assert datetime(2013, 1, 2) == field_tester.field_a
    del field_tester.field_a
    assert field_tester.field_a is None

    # Test default explicitly specified
    field_tester.field_b = datetime(2013, 1, 2)
    assert datetime(2013, 1, 2) == field_tester.field_b
    del field_tester.field_b
    assert datetime(2013, 4, 1) == field_tester.field_b


def test_defaults_not_shared():
    class FieldTester(XBlock):
        """Toy class for field access testing"""

        field_a = List(scope=Scope.settings)

    field_tester_a = FieldTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))
    field_tester_b = FieldTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))

    field_tester_a.field_a.append(1)
    assert [1] == field_tester_a.field_a
    assert [] == field_tester_b.field_a
    # Write out the data
    field_tester_a.save()
    # Double check that write didn't do something weird
    assert [1] == field_tester_a.field_a
    assert [] == field_tester_b.field_a


def test_object_identity():
    # Check that values that are modified are what is returned
    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""
        field_a = List(scope=Scope.settings)

    def mock_default(block, name):  # pylint: disable=unused-argument
        """
        Raising KeyError emulates no attribute found, which causes
        proper default value to be used after field is deleted.
        """
        raise KeyError

    # Make sure that field_data always returns a different object
    # each time it's actually queried, so that the caching is
    # doing the work to maintain object identity.
    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322
    field_data.default = mock_default
    field_tester = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )
    value = field_tester.field_a
    assert value == field_tester.field_a

    # Changing the field in place matches a previously fetched value
    field_tester.field_a.append(1)
    assert value == field_tester.field_a

    # Changing the previously-fetched value also changes the value returned by the field:
    value.append(2)
    assert value == field_tester.field_a

    # Deletion restores the default value.  In the case of a List with
    # no default defined, this is the empty list.
    del field_tester.field_a
    assert [] == field_tester.field_a


def test_caching_is_per_instance():
    # Test that values cached for one instance do not appear on another
    class FieldTester(ScopedStorageMixin):
        """Toy class for ModelMetaclass and field access testing"""
        field_a = List(scope=Scope.settings)

    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: [name]  # pylint: disable=C0322

    # Same field_data used in different objects should result
    # in separately-cached values, so that changing a value
    # in one instance doesn't affect values stored in others.
    field_tester_a = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )
    field_tester_b = FieldTester(
        runtime=TestRuntime(services={'field-data': field_data}),
        scope_ids=MagicMock(spec=ScopeIds)
    )
    value = field_tester_a.field_a
    assert value == field_tester_a.field_a
    field_tester_a.field_a.append(1)
    assert value == field_tester_a.field_a
    assert value != field_tester_b.field_a


def test_field_serialization():
    # Some Fields can define their own serialization mechanisms.
    # This test ensures that we are using them properly.

    class CustomField(Field):
        """
        Specify a custom field that defines its own serialization
        """
        def from_json(self, value):
            return value['value']

        def to_json(self, value):
            return {'value': value}

    class FieldTester(XBlock):
        """Test XBlock for field serialization testing"""
        field = CustomField()

    field_data = DictFieldData({
        'field': {'value': 4}
    })

    field_tester = FieldTester(
        TestRuntime(services={'field-data': field_data}),
        None,
        Mock(),
    )

    assert field_tester.field == 4
    field_tester.field = 5
    field_tester.save()
    assert {'value': 5} == field_data.get(field_tester, 'field')


def test_class_tags():
    xblock = XBlock(None, None, None)
    assert xblock._class_tags == set()

    class Sub1Block(XBlock):
        """Toy XBlock"""
        pass

    sub1block = Sub1Block(None, None, None)
    assert sub1block._class_tags == set()

    @XBlock.tag("cat dog")
    class Sub2Block(Sub1Block):
        """Toy XBlock"""
        pass

    sub2block = Sub2Block(None, None, None)
    assert sub2block._class_tags == set(["cat", "dog"])

    class Sub3Block(Sub2Block):
        """Toy XBlock"""
        pass

    sub3block = Sub3Block(None, None, None)
    assert sub3block._class_tags == set(["cat", "dog"])

    @XBlock.tag("mixin")
    class MixinBlock(XBlock):
        """Toy XBlock"""
        pass

    class Sub4Block(MixinBlock, Sub3Block):
        """Toy XBlock"""
        pass

    sub4block = Sub4Block(None, None, None)
    assert sub4block._class_tags == set(["cat", "dog", "mixin"])


def test_loading_tagged_classes():

    @XBlock.tag("thetag")
    class HasTag1(XBlock):
        """Toy XBlock"""
        pass

    class HasTag2(HasTag1):
        """Toy XBlock"""
        pass

    class HasntTag(XBlock):
        """Toy XBlock"""
        pass

    the_classes = [('hastag1', HasTag1), ('hastag2', HasTag2), ('hasnttag', HasntTag)]
    tagged_classes = [('hastag1', HasTag1), ('hastag2', HasTag2)]
    with patch('xblock.core.XBlock.load_classes', return_value=the_classes):
        assert set(XBlock.load_tagged_classes('thetag')) == set(tagged_classes)


def setup_save_failure(set_many):
    """
    Set up tests for when there's a save error in the underlying KeyValueStore
    """
    field_data = MagicMock(spec=FieldData)
    field_data.get = lambda block, name, default=None: 99  # pylint: disable=C0322

    field_data.set_many = set_many

    class FieldTester(XBlock):
        """
        Test XBlock with three fields
        """
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)
        field_c = Integer(scope=Scope.user_state, default=42)

    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))
    return field_tester


def test_xblock_save_one():
    # Mimics a save failure when we only manage to save one of the values

    def fake_set_many(block, update_dict):  # pylint: disable=unused-argument
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that only one field was correctly saved."""
        raise KeyValueMultiSaveError([next(iter(update_dict))])

    field_tester = setup_save_failure(fake_set_many)

    field_tester.field_a = 20
    field_tester.field_b = 40
    field_tester.field_c = 60

    with pytest.raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

    # Verify that the correct data is getting stored by the error
    assert len(save_error.value.saved_fields) == 1
    assert len(save_error.value.dirty_fields) == 2


def test_xblock_save_failure_none():
    # Mimics a save failure when we don't manage to save any of the values

    def fake_set_many(block, update_dict):  # pylint: disable=unused-argument
        """Mock update method that throws a KeyValueMultiSaveError indicating
           that no fields were correctly saved."""
        raise KeyValueMultiSaveError([])

    field_tester = setup_save_failure(fake_set_many)
    field_tester.field_a = 20
    field_tester.field_b = 30
    field_tester.field_c = 40

    with pytest.raises(XBlockSaveError) as save_error:
        # This call should raise an XBlockSaveError
        field_tester.save()

    # Verify that the correct data is getting stored by the error
    assert len(save_error.value.saved_fields) == 0
    assert len(save_error.value.dirty_fields) == 3


def test_xblock_write_then_delete():
    # Tests that setting a field, then deleting it later, doesn't
    # cause an erroneous write of the originally set value after
    # a call to `XBlock.save`
    class FieldTester(XBlock):
        """Test XBlock with two fields"""
        field_a = Integer(scope=Scope.settings)
        field_b = Integer(scope=Scope.content, default=10)

    field_data = DictFieldData({'field_a': 5})
    field_tester = FieldTester(TestRuntime(services={'field-data': field_data}), scope_ids=Mock(spec=ScopeIds))

    # Verify that the fields have been set correctly
    assert field_tester.field_a == 5
    assert field_tester.field_b == 10

    # Set the fields to new values
    field_tester.field_a = 20
    field_tester.field_b = 20

    # Assert that we've correctly cached the value of both fields to the newly set values.
    assert field_tester.field_a == 20
    assert field_tester.field_b == 20

    # Before saving, delete all the fields. Deletes are performed immediately for now,
    # so the field should immediately not be present in the field_data after the delete.
    # However, we copy the default values into the cache, so after the delete we expect the
    # cached values to be the default values, but the fields to be removed from the field_data.
    del field_tester.field_a
    del field_tester.field_b

    # Assert that we're now finding the right cached values - these should be the default values
    # that the fields have from the class since we've performed a delete, and XBlock.__delete__
    # inserts the default values into the cache as an optimization.
    assert field_tester.field_a is None
    assert field_tester.field_b == 10

    # Perform explicit save
    field_tester.save()

    # Now that we've done the save, double-check that we still have the correct cached values (the defaults)
    assert field_tester.field_a is None
    assert field_tester.field_b == 10

    # Additionally assert that in the model data, we don't have any values actually set for these fields.
    # Basically, we want to ensure that the `save` didn't overwrite anything in the actual field_data
    # Note this test directly accessess field_data and is thus somewhat fragile.
    assert not field_data.has(field_tester, 'field_a')
    assert not field_data.has(field_tester, 'field_b')


def test_get_mutable_mark_dirty():
    """
    Ensure that accessing a mutable field type does not mark it dirty
    if the field has never been set. If the field has been set, ensure
    that it is set to dirty.
    """
    class MutableTester(XBlock):
        """Test class with mutable fields."""
        list_field = List(default=[])

    mutable_test = MutableTester(TestRuntime(services={'field-data': DictFieldData({})}), scope_ids=Mock(spec=ScopeIds))

    # Test get/set with a default value.
    assert len(mutable_test._dirty_fields) == 0
    _test_get = mutable_test.list_field
    assert len(mutable_test._dirty_fields) == 1

    mutable_test.list_field = []
    assert len(mutable_test._dirty_fields) == 1

    # Now test after having explicitly set the field.
    mutable_test.save()
    # _dirty_fields shouldn't be cleared here
    assert len(mutable_test._dirty_fields) == 1
    _test_get = mutable_test.list_field
    assert len(mutable_test._dirty_fields) == 1


def test_change_mutable_default():
    """
    Ensure that mutating the default value for a field causes
    the changes to be saved, and doesn't corrupt other instances
    """

    class MutableTester(XBlock):
        """Test class with mutable fields."""
        list_field = List()

    field_data_a = DictFieldData({})
    mutable_test_a = MutableTester(TestRuntime(services={'field-data': field_data_a}), scope_ids=Mock(spec=ScopeIds))
    field_data_b = DictFieldData({})
    mutable_test_b = MutableTester(TestRuntime(services={'field-data': field_data_b}), scope_ids=Mock(spec=ScopeIds))

    # Saving without changing the default value shouldn't write to field_data
    mutable_test_a.list_field  # pylint: disable=W0104
    mutable_test_a.save()
    with pytest.raises(KeyError):
        field_data_a.get(mutable_test_a, 'list_field')

    mutable_test_a.list_field.append(1)
    mutable_test_a.save()

    assert [1] == field_data_a.get(mutable_test_a, 'list_field')
    with pytest.raises(KeyError):
        field_data_b.get(mutable_test_b, 'list_field')


def test_handle_shortcut():
    runtime = Mock(spec=['handle'])
    scope_ids = Mock(spec=[])
    request = Mock(spec=[])
    block = XBlock(runtime, None, scope_ids)

    block.handle('handler_name', request)
    runtime.handle.assert_called_with(block, 'handler_name', request, '')

    runtime.handle.reset_mock()
    block.handle('handler_name', request, 'suffix')
    runtime.handle.assert_called_with(block, 'handler_name', request, 'suffix')


def test_services_decorators():
    # pylint: disable=E1101
    # A default XBlock has requested no services
    xblock = XBlock(None, None, None)
    assert XBlock._services_requested == {}
    assert xblock._services_requested == {}

    @XBlock.needs("n")
    @XBlock.wants("w")
    class ServiceUsingBlock(XBlock):
        """XBlock using some services."""
        pass

    service_using_block = ServiceUsingBlock(None, scope_ids=None)
    assert ServiceUsingBlock._services_requested == {'n': 'need', 'w': 'want'}
    assert service_using_block._services_requested == {'n': 'need', 'w': 'want'}


def test_services_decorators_with_inheritance():
    @XBlock.needs("n1")
    @XBlock.wants("w1")
    class ServiceUsingBlock(XBlock):
        """XBlock using some services."""
        pass

    @XBlock.needs("n2")
    @XBlock.wants("w2")
    class SubServiceUsingBlock(ServiceUsingBlock):
        """Does this class properly inherit services from ServiceUsingBlock?"""
        pass

    sub_service_using_block = SubServiceUsingBlock(None, scope_ids=None)
    assert sub_service_using_block.service_declaration("n1") == "need"
    assert sub_service_using_block.service_declaration("w1") == "want"
    assert sub_service_using_block.service_declaration("n2") == "need"
    assert sub_service_using_block.service_declaration("w2") == "want"
    assert sub_service_using_block.service_declaration("xx") is None


def test_cached_parent():
    class HasParent(XBlock):
        """
        Dummy empty class
        """
        pass

    runtime = TestRuntime(services={'field-data': DictFieldData({})})
    runtime.get_block = Mock()
    block = HasParent(runtime, scope_ids=Mock(spec=ScopeIds))

    # block has no parent yet, and we don't need to call the runtime to find
    # that out.
    assert block.get_parent() is None
    assert not runtime.get_block.called

    # Set a parent id for the block.  Get the parent.  Now we have one, and we
    # used runtime.get_block to get it.
    block.parent = "some_parent_id"
    parent = block.get_parent()
    assert parent is not None
    assert runtime.get_block.called_with("some_parent_id")

    # Get the parent again.  It will be the same parent, and we didn't call the
    # runtime.
    runtime.get_block.reset_mock()
    parent2 = block.get_parent()
    assert parent2 is parent
    assert not runtime.get_block.called


def test_json_handler_basic():
    test_self = Mock()
    test_data = {"foo": "bar", "baz": "quux"}
    test_data_json = ['{"foo": "bar", "baz": "quux"}', '{"baz": "quux", "foo": "bar"}']
    test_suffix = "suff"
    test_request = Mock(method="POST", body=test_data_json[0])

    @XBlock.json_handler
    def test_func(self, request, suffix):
        assert self == test_self
        assert request == test_data
        assert suffix == test_suffix
        return request

    response = test_func(test_self, test_request, test_suffix)
    assert response.status_code == 200
    assert response.body.decode('utf-8') in test_data_json
    assert response.content_type == "application/json"


def test_json_handler_invalid_json():
    test_request = Mock(method="POST", body="{")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert response.status_code == 400
    assert json.loads(response.body.decode('utf-8')) == {"error": "Invalid JSON"}
    assert response.content_type == "application/json"


def test_json_handler_get():
    test_request = Mock(method="GET")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert response.status_code == 405
    assert json.loads(response.body.decode('utf-8')) == {"error": "Method must be POST"}
    assert list(response.allow) == ["POST"]


def test_json_handler_empty_request():
    test_request = Mock(method="POST", body="")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        return {}

    response = test_func(Mock(), test_request, "dummy_suffix")
    # pylint: disable=no-member
    assert response.status_code == 400
    assert json.loads(response.body.decode('utf-8')) == {"error": "Invalid JSON"}
    assert response.content_type == "application/json"


def test_json_handler_error():
    test_status_code = 418
    test_message = "I'm a teapot"
    test_request = Mock(method="POST", body="{}")

    @XBlock.json_handler
    def test_func(self, request, suffix):   # pylint: disable=unused-argument
        raise JsonHandlerError(test_status_code, test_message)

    response = test_func(Mock(), test_request, "dummy_suffix")  # pylint: disable=assignment-from-no-return
    assert response.status_code == test_status_code
    assert json.loads(response.body.decode('utf-8')) == {"error": test_message}
    assert response.content_type == "application/json"


def test_json_handler_return_response():
    test_request = Mock(method="POST", body="{}")

    @XBlock.json_handler
    def test_func(self, request, suffix):  # pylint: disable=unused-argument
        return Response(body="not JSON", status=418, content_type="text/plain")

    response = test_func(Mock(), test_request, "dummy_suffix")
    assert response.ubody == "not JSON"
    assert response.status_code == 418
    assert response.content_type == "text/plain"


def test_json_handler_return_unicode():
    test_request = Mock(method="POST", body='["foo", "bar"]')

    @XBlock.json_handler
    def test_func(self, request, suffix):  # pylint: disable=unused-argument
        return Response(request=request)

    response = test_func(Mock(), test_request, "dummy_suffix")
    for request_part in response.request:  # pylint: disable=not-an-iterable
        assert isinstance(request_part, six.text_type)


@ddt.ddt
class OpenLocalResourceTest(unittest.TestCase):
    """Tests of `open_local_resource`."""

    class LoadableXBlock(XBlock):
        """Just something to load resources from."""
        pass

    class UnloadableXBlock(XBlock):
        """Just something to load resources from."""
        resources_dir = None

    def stub_resource_stream(self, module, name):
        """Act like pkg_resources.resource_stream, for testing."""
        assert module == "xblock.test.test_core"
        return "!" + name + "!"

    @ddt.data(
        "public/hey.js",
        "public/sub/hey.js",
        "public/js/vendor/jNotify.jQuery.min.js",
        "public/something.foo",         # Unknown file extension is fine
        "public/a/long/PATH/no-problem=here$123.ext",
        "public/\N{SNOWMAN}.js",
    )
    def test_open_good_local_resource(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            assert loadable.open_local_resource(uri) == "!" + uri + "!"
            assert loadable.open_local_resource(uri.encode('utf-8')) == "!" + uri + "!"

    @ddt.data(
        "public/hey.js".encode('utf-8'),
        "public/sub/hey.js".encode('utf-8'),
        "public/js/vendor/jNotify.jQuery.min.js".encode('utf-8'),
        "public/something.foo".encode('utf-8'),         # Unknown file extension is fine
        "public/a/long/PATH/no-problem=here$123.ext".encode('utf-8'),
        "public/\N{SNOWMAN}.js".encode('utf-8'),
    )
    def test_open_good_local_resource_binary(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            assert loadable.open_local_resource(uri) == "!" + uri.decode('utf-8') + "!"

    @ddt.data(
        "public/../secret.js",
        "public/.git/secret.js",
        "static/secret.js",
        "../public/no-no.bad",
        "image.png",
        ".git/secret.js",
        "static/\N{SNOWMAN}.js",
    )
    def test_open_bad_local_resource(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            msg_pattern = ".*: %s" % re.escape(repr(uri))
            with pytest.raises(DisallowedFileError, match=msg_pattern):
                loadable.open_local_resource(uri)

    @ddt.data(
        "public/../secret.js".encode('utf-8'),
        "public/.git/secret.js".encode('utf-8'),
        "static/secret.js".encode('utf-8'),
        "../public/no-no.bad".encode('utf-8'),
        "image.png".encode('utf-8'),
        ".git/secret.js".encode('utf-8'),
        "static/\N{SNOWMAN}.js".encode('utf-8'),
    )
    def test_open_bad_local_resource_binary(self, uri):
        loadable = self.LoadableXBlock(None, scope_ids=None)
        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            msg = ".*: %s" % re.escape(repr(uri.decode('utf-8')))
            with pytest.raises(DisallowedFileError, match=msg):
                loadable.open_local_resource(uri)

    @ddt.data(
        "public/hey.js",
        "public/sub/hey.js",
        "public/js/vendor/jNotify.jQuery.min.js",
        "public/something.foo",         # Unknown file extension is fine
        "public/a/long/PATH/no-problem=here$123.ext",
        "public/\N{SNOWMAN}.js",
        "public/foo.js",
        "public/.git/secret.js",
        "static/secret.js",
        "../public/no-no.bad",
        "image.png",
        ".git/secret.js",
        "static/\N{SNOWMAN}.js",
    )
    def test_open_local_resource_with_no_resources_dir(self, uri):
        unloadable = self.UnloadableXBlock(None, scope_ids=None)

        with patch('pkg_resources.resource_stream', self.stub_resource_stream):
            msg = "not configured to serve local resources"
            with pytest.raises(DisallowedFileError, match=msg):
                unloadable.open_local_resource(uri)


class TestXBlockDeprecation(WarningTestMixin, unittest.TestCase):
    """
    Tests various pieces of XBlock that have been (or will be) deprecated.
    """

    class TestBlock(XBlock):
        """An empty XBlock for testing"""
        pass

    def test_field_data_paramater(self):
        field_data = Mock(spec=FieldData)
        with self.assertWarns(FieldDataDeprecationWarning):
            block = XBlock(Mock(spec=Runtime), field_data, Mock(spec=ScopeIds))
        self.assertEqual(field_data, block._field_data)

    def test_assign_field_data(self):
        field_data = Mock(spec=FieldData)
        block = XBlock(Mock(spec=Runtime), scope_ids=Mock(spec=ScopeIds))
        with self.assertWarns(FieldDataDeprecationWarning):
            block._field_data = field_data
        self.assertEqual(field_data, block._field_data)


class TestIndexResults(unittest.TestCase):
    """
    Tests to confirm that default block has empty index, and that XBlocks can provide custom index dictionary
    """

    class TestXBlock(XBlock):
        """
        Class to test default Xblock provides a dictionary
        """
        pass

    class TestIndexedXBlock(XBlock):
        """
        Class to test when an Xblock provides a dictionary
        """

        def index_dictionary(self):
            return {
                "test_field": "ABC123",
                "text_block": "Here is some text that was indexed",
            }

    def test_default_index_view(self):
        test_runtime = TestRuntime(services={'field-data': DictFieldData({})})
        test_xblock = self.TestXBlock(test_runtime, scope_ids=Mock(spec=ScopeIds))

        index_info = test_xblock.index_dictionary()
        self.assertFalse(index_info)
        self.assertTrue(isinstance(index_info, dict))

    def test_override_index_view(self):
        test_runtime = TestRuntime(services={'field-data': DictFieldData({})})
        test_xblock = self.TestIndexedXBlock(test_runtime, scope_ids=Mock(spec=ScopeIds))

        index_info = test_xblock.index_dictionary()
        self.assertTrue(index_info)
        self.assertTrue(isinstance(index_info, dict))
        self.assertEqual(index_info["test_field"], "ABC123")
