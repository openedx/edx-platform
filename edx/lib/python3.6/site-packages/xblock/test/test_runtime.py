# -*- coding: utf-8 -*-
"""Tests the features of xblock/runtime"""

from __future__ import absolute_import, division, print_function, unicode_literals

# pylint: disable=protected-access

from datetime import datetime
from unittest import TestCase

from mock import Mock, patch
import pytest
import six

from web_fragments.fragment import Fragment

from xblock.core import XBlock, XBlockMixin
from xblock.exceptions import (
    NoSuchDefinition,
    NoSuchHandlerError,
    NoSuchServiceError,
    NoSuchUsage,
    NoSuchViewError,
    FieldDataDeprecationWarning,
)
from xblock.fields import BlockScope, Scope, String, ScopeIds, List, UserScope, Integer
from xblock.runtime import (
    DictKeyValueStore,
    IdReader,
    KeyValueStore,
    KvsFieldData,
    Mixologist,
    ObjectAggregator,
)
from xblock.field_data import DictFieldData, FieldData

from xblock.test.tools import unabc, WarningTestMixin, TestRuntime


class TestMixin(object):
    """
    Set up namespaces for each scope to use.
    """
    mixin_content = String(scope=Scope.content, default='mixin_c')
    mixin_settings = String(scope=Scope.settings, default='mixin_s')
    mixin_user_state = String(scope=Scope.user_state, default='mixin_ss')
    mixin_preferences = String(scope=Scope.preferences, default='mixin_sp')
    mixin_user_info = String(scope=Scope.user_info, default='mixin_si')
    mixin_by_type = String(scope=Scope(UserScope.NONE, BlockScope.TYPE), default='mixin_bt')
    mixin_for_all = String(scope=Scope(UserScope.NONE, BlockScope.ALL), default='mixin_fa')
    mixin_user_def = String(scope=Scope(UserScope.ONE, BlockScope.DEFINITION), default='mixin_sd')
    mixin_agg_global = String(scope=Scope(UserScope.ALL, BlockScope.ALL), default='mixin_ag')
    mixin_agg_type = String(scope=Scope(UserScope.ALL, BlockScope.TYPE), default='mixin_at')
    mixin_agg_def = String(scope=Scope(UserScope.ALL, BlockScope.DEFINITION), default='mixin_ad')
    mixin_agg_usage = String(scope=Scope.user_state_summary, default='mixin_au')


class TestXBlockNoFallback(XBlock):
    """
    Set up a class that contains ModelTypes as fields, but no views or handlers
    """
    __test__ = False
    content = String(scope=Scope.content, default='c')
    settings = String(scope=Scope.settings, default='s')
    user_state = String(scope=Scope.user_state, default='ss')
    preferences = String(scope=Scope.preferences, default='sp')
    user_info = String(scope=Scope.user_info, default='si')
    by_type = String(scope=Scope(UserScope.NONE, BlockScope.TYPE), default='bt')
    for_all = String(scope=Scope(UserScope.NONE, BlockScope.ALL), default='fa')
    user_def = String(scope=Scope(UserScope.ONE, BlockScope.DEFINITION), default='sd')
    agg_global = String(scope=Scope(UserScope.ALL, BlockScope.ALL), default='ag')
    agg_type = String(scope=Scope(UserScope.ALL, BlockScope.TYPE), default='at')
    agg_def = String(scope=Scope(UserScope.ALL, BlockScope.DEFINITION), default='ad')
    agg_usage = String(scope=Scope.user_state_summary, default='au')

    def handler_without_correct_decoration(self, request, suffix=''):
        """a handler which is missing the @XBlock.handler decoration."""
        pass


class TestXBlock(TestXBlockNoFallback):
    """
    Test xblock class with fallback methods
    """
    @XBlock.handler
    def existing_handler(self, request, suffix=''):  # pylint: disable=unused-argument
        """ an existing handler to be used """
        self.user_state = request
        return "I am the existing test handler"

    @XBlock.handler
    def fallback_handler(self, handler_name, request, suffix=''):  # pylint: disable=unused-argument
        """ test fallback handler """
        self.user_state = request
        if handler_name == 'test_fallback_handler':
            return "I have been handled"
        if handler_name == 'handler_without_correct_decoration':
            return "gone to fallback"
        return "unhandled!!"

    def student_view(self, context):
        """ an existing view to be used """
        self.preferences = context[0]
        return Fragment(self.preferences)

    def fallback_view(self, view_name, context):
        """ test fallback view """
        self.preferences = context[0]
        if view_name == 'test_fallback_view':
            return Fragment(self.preferences)
        else:
            return Fragment("{} default".format(view_name))


def test_db_model_keys():
    # Tests that updates to fields are properly recorded in the KeyValueStore,
    # and that the keys have been constructed correctly
    key_store = DictKeyValueStore()
    field_data = KvsFieldData(key_store)
    runtime = TestRuntime(Mock(), mixins=[TestMixin], services={'field-data': field_data})
    tester = runtime.construct_xblock_from_class(TestXBlock, ScopeIds('s0', 'TestXBlock', 'd0', 'u0'))

    assert not field_data.has(tester, 'not a field')

    for field in six.itervalues(tester.fields):
        new_value = 'new ' + field.name
        assert not field_data.has(tester, field.name)
        if isinstance(field, List):
            new_value = [new_value]
        setattr(tester, field.name, new_value)

    # Write out the values
    tester.save()

    # Make sure everything saved correctly
    for field in six.itervalues(tester.fields):
        assert field_data.has(tester, field.name)

    def get_key_value(scope, user_id, block_scope_id, field_name):
        """Gets the value, from `key_store`, of a Key with the given values."""
        new_key = KeyValueStore.Key(scope, user_id, block_scope_id, field_name)
        return key_store.db_dict[new_key]

    # Examine each value in the database and ensure that keys were constructed correctly
    assert get_key_value(Scope.content, None, 'd0', 'content') == 'new content'
    assert get_key_value(Scope.settings, None, 'u0', 'settings') == 'new settings'
    assert get_key_value(Scope.user_state, 's0', 'u0', 'user_state') == 'new user_state'
    assert get_key_value(Scope.preferences, 's0', 'TestXBlock', 'preferences') == 'new preferences'
    assert get_key_value(Scope.user_info, 's0', None, 'user_info') == 'new user_info'
    assert get_key_value(Scope(UserScope.NONE, BlockScope.TYPE), None, 'TestXBlock', 'by_type') == 'new by_type'
    assert get_key_value(Scope(UserScope.NONE, BlockScope.ALL), None, None, 'for_all') == 'new for_all'
    assert get_key_value(Scope(UserScope.ONE, BlockScope.DEFINITION), 's0', 'd0', 'user_def') == 'new user_def'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.ALL), None, None, 'agg_global') == 'new agg_global'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.TYPE), None, 'TestXBlock', 'agg_type') == 'new agg_type'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.DEFINITION), None, 'd0', 'agg_def') == 'new agg_def'
    assert get_key_value(Scope.user_state_summary, None, 'u0', 'agg_usage') == 'new agg_usage'
    assert get_key_value(Scope.content, None, 'd0', 'mixin_content') == 'new mixin_content'
    assert get_key_value(Scope.settings, None, 'u0', 'mixin_settings') == 'new mixin_settings'
    assert get_key_value(Scope.user_state, 's0', 'u0', 'mixin_user_state') == 'new mixin_user_state'
    assert get_key_value(Scope.preferences, 's0', 'TestXBlock', 'mixin_preferences') == 'new mixin_preferences'
    assert get_key_value(Scope.user_info, 's0', None, 'mixin_user_info') == 'new mixin_user_info'
    assert get_key_value(Scope(UserScope.NONE, BlockScope.TYPE), None, 'TestXBlock', 'mixin_by_type') == \
        'new mixin_by_type'
    assert get_key_value(Scope(UserScope.NONE, BlockScope.ALL), None, None, 'mixin_for_all') == \
        'new mixin_for_all'
    assert get_key_value(Scope(UserScope.ONE, BlockScope.DEFINITION), 's0', 'd0', 'mixin_user_def') == \
        'new mixin_user_def'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.ALL), None, None, 'mixin_agg_global') == \
        'new mixin_agg_global'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.TYPE), None, 'TestXBlock', 'mixin_agg_type') == \
        'new mixin_agg_type'
    assert get_key_value(Scope(UserScope.ALL, BlockScope.DEFINITION), None, 'd0', 'mixin_agg_def') == \
        'new mixin_agg_def'
    assert get_key_value(Scope.user_state_summary, None, 'u0', 'mixin_agg_usage') == 'new mixin_agg_usage'


@unabc("{} shouldn't be used in tests")
class MockRuntimeForQuerying(TestRuntime):
    """Mock out a runtime for querypath_parsing test"""
    # unabc doesn't squash pylint errors
    # pylint: disable=abstract-method
    def __init__(self, **kwargs):
        self.mock_query = Mock()
        super(MockRuntimeForQuerying, self).__init__(**kwargs)

    def query(self, block):
        return self.mock_query


def test_querypath_parsing():
    mrun = MockRuntimeForQuerying()
    block = Mock()
    mrun.querypath(block, "..//@hello")
    print(mrun.mock_query.mock_calls)
    expected = Mock()
    expected.parent().descendants().attr("hello")
    assert mrun.mock_query.mock_calls == expected.mock_calls


def test_runtime_handle():
    # Test a simple handler and a fallback handler

    key_store = DictKeyValueStore()
    field_data = KvsFieldData(key_store)
    test_runtime = TestRuntime(services={'field-data': field_data})
    basic_tester = TestXBlock(test_runtime, scope_ids=Mock(spec=ScopeIds))
    runtime = MockRuntimeForQuerying()
    # string we want to update using the handler
    update_string = "user state update"
    assert runtime.handle(basic_tester, 'existing_handler', update_string) == \
        'I am the existing test handler'
    assert basic_tester.user_state == update_string

    # when the handler needs to use the fallback as given name can't be found
    new_update_string = "new update"
    assert runtime.handle(basic_tester, 'test_fallback_handler', new_update_string) == \
        'I have been handled'
    assert basic_tester.user_state == new_update_string

    # request to use a handler which doesn't have XBlock.handler decoration
    # should use the fallback
    new_update_string = "new update"
    assert runtime.handle(basic_tester, 'handler_without_correct_decoration', new_update_string) == \
        'gone to fallback'
    assert basic_tester.user_state == new_update_string

    # handler can't be found & no fallback handler supplied, should throw an exception
    no_fallback_tester = TestXBlockNoFallback(runtime, scope_ids=Mock(spec=ScopeIds))
    ultimate_string = "ultimate update"
    with pytest.raises(NoSuchHandlerError):
        runtime.handle(no_fallback_tester, 'test_nonexistant_fallback_handler', ultimate_string)

    # request to use a handler which doesn't have XBlock.handler decoration
    # and no fallback should raise NoSuchHandlerError
    with pytest.raises(NoSuchHandlerError):
        runtime.handle(no_fallback_tester, 'handler_without_correct_decoration', 'handled')


def test_runtime_render():
    key_store = DictKeyValueStore()
    field_data = KvsFieldData(key_store)
    runtime = MockRuntimeForQuerying(services={'field-data': field_data})
    block_type = 'test'
    def_id = runtime.id_generator.create_definition(block_type)
    usage_id = runtime.id_generator.create_usage(def_id)
    tester = TestXBlock(runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))
    # string we want to update using the handler
    update_string = "user state update"

    # test against the student view
    frag = runtime.render(tester, 'student_view', [update_string])
    assert update_string in frag.body_html()
    assert tester.preferences == update_string

    # test against the fallback view
    update_string = "new update"
    frag = runtime.render(tester, 'test_fallback_view', [update_string])
    assert update_string in frag.body_html()
    assert tester.preferences == update_string

    # test block-first
    update_string = "penultimate update"
    frag = tester.render('student_view', [update_string])
    assert update_string in frag.body_html()
    assert tester.preferences == update_string

    # test against the no-fallback XBlock
    update_string = "ultimate update"
    no_fallback_tester = TestXBlockNoFallback(Mock(), scope_ids=Mock(spec=ScopeIds))
    with pytest.raises(NoSuchViewError):
        runtime.render(no_fallback_tester, 'test_nonexistent_view', [update_string])


class SerialDefaultKVS(DictKeyValueStore):
    """
    A kvs which gives each call to default the next int (nonsensical but for testing default fn)
    """
    def __init__(self, *args, **kwargs):
        super(SerialDefaultKVS, self).__init__(*args, **kwargs)
        self.default_counter = 0

    def default(self, _key):
        self.default_counter += 1
        return self.default_counter


class TestIntegerXblock(XBlock):
    """
    XBlock with an integer field, for testing.
    """
    __test__ = False
    counter = Integer(scope=Scope.content)


def test_default_fn():
    key_store = SerialDefaultKVS()
    field_data = KvsFieldData(key_store)
    runtime = TestRuntime(services={'field-data': field_data})
    tester = TestIntegerXblock(runtime, scope_ids=Mock(spec=ScopeIds))
    tester2 = TestIntegerXblock(runtime, scope_ids=Mock(spec=ScopeIds))

    # ensure value is not in tester before any actions
    assert not field_data.has(tester, 'counter')
    # ensure value is same over successive calls for same DbModel
    first_call = tester.counter
    assert first_call == 1
    assert first_call == tester.counter
    # ensure the value is not saved in the object
    assert not field_data.has(tester, 'counter')
    # ensure save does not save the computed default back to the object
    tester.save()
    assert not field_data.has(tester, 'counter')

    # ensure second object gets another value
    second_call = tester2.counter
    assert second_call == 2


class TestSimpleMixin(object):
    """Toy class for mixin testing"""
    field_x = List(scope=Scope.content)
    field_y = String(scope=Scope.user_state, default="default_value")

    @property
    def field_x_with_default(self):
        """
        Test method for generating programmatic default values for fields
        """
        return self.field_x or [1, 2, 3]


class FieldTester(XBlock):
    """Test XBlock for field access testing"""
    field_a = Integer(scope=Scope.settings)
    field_b = Integer(scope=Scope.content, default=10)
    field_c = Integer(scope=Scope.user_state, default=42)


# Test that access to fields from mixins works as expected
def test_mixin_field_access():
    field_data = DictFieldData({
        'field_a': 5,
        'field_x': [1, 2, 3],
    })
    runtime = TestRuntime(Mock(), mixins=[TestSimpleMixin], services={'field-data': field_data})

    field_tester = runtime.construct_xblock_from_class(FieldTester, Mock())

    assert field_tester.field_a == 5
    assert field_tester.field_b == 10
    assert field_tester.field_c == 42
    assert field_tester.field_x == [1, 2, 3]
    assert field_tester.field_y == 'default_value'

    field_tester.field_x = ['a', 'b']
    field_tester.save()
    assert ['a', 'b'] == field_tester._field_data.get(field_tester, 'field_x')

    del field_tester.field_x
    assert [] == field_tester.field_x
    assert [1, 2, 3] == field_tester.field_x_with_default

    with pytest.raises(AttributeError):
        getattr(field_tester, 'field_z')
    with pytest.raises(AttributeError):
        delattr(field_tester, 'field_z')

    field_tester.field_z = 'foo'
    assert field_tester.field_z == 'foo'
    assert not field_tester._field_data.has(field_tester, 'field_z')


class Dynamic(object):
    """
    Object for testing that sets attrs based on __init__ kwargs
    """
    def __init__(self, **kwargs):
        for name, value in six.iteritems(kwargs):
            setattr(self, name, value)


class TestObjectAggregator(object):
    """
    Test that the ObjectAggregator behaves correctly
    """
    # pylint: disable=attribute-defined-outside-init
    def setup_method(self):
        """
        Setup for each test method in this class.
        """
        # Create some objects that only have single attributes
        self.first = Dynamic(first=1)
        self.second = Dynamic(second=2)
        self.agg = ObjectAggregator(self.first, self.second)
    # pylint: enable=attribute-defined-outside-init

    def test_get(self):
        assert self.agg.first == 1
        assert self.agg.second == 2
        assert not hasattr(self.agg, 'other')
        with pytest.raises(AttributeError):
            self.agg.other  # pylint: disable=W0104

    def test_set(self):
        assert self.agg.first == 1
        self.agg.first = 10
        assert self.agg.first == 10
        assert self.first.first == 10  # pylint: disable=E1101

        with pytest.raises(AttributeError):
            self.agg.other = 99
        assert not hasattr(self.first, 'other')
        assert not hasattr(self.second, 'other')

    def test_delete(self):
        assert self.agg.first == 1
        del self.agg.first
        assert not hasattr(self.first, 'first')
        with pytest.raises(AttributeError):
            self.agg.first  # pylint: disable=W0104

        with pytest.raises(AttributeError):
            del self.agg.other


class FirstMixin(XBlockMixin):
    """Test class for mixin ordering."""
    number = 1
    field = Integer(default=1)


class SecondMixin(XBlockMixin):
    """Test class for mixin ordering."""
    number = 2
    field = Integer(default=2)


class ThirdMixin(XBlockMixin):
    """Test class for mixin ordering."""
    field = Integer(default=3)


class TestMixologist(object):
    """Test that the Mixologist class behaves correctly."""
    def setup_method(self):
        """
        Setup for each test method in this class.
        """
        self.mixologist = Mixologist([FirstMixin, SecondMixin])  # pylint: disable=attribute-defined-outside-init

    # Test that the classes generated by the mixologist are cached
    # (and only generated once)
    def test_only_generate_classes_once(self):
        assert self.mixologist.mix(FieldTester) is self.mixologist.mix(FieldTester)
        assert not self.mixologist.mix(FieldTester) is self.mixologist.mix(TestXBlock)

    # Test that mixins are applied in order
    def test_mixin_order(self):
        assert 1 is self.mixologist.mix(FieldTester).number
        assert 1 is self.mixologist.mix(FieldTester).fields['field'].default

    def test_unmixed_class(self):
        assert FieldTester is self.mixologist.mix(FieldTester).unmixed_class

    def test_mixin_fields(self):
        assert FirstMixin.fields['field'] is FirstMixin.field  # pylint: disable=unsubscriptable-object

    def test_mixed_fields(self):
        mixed = self.mixologist.mix(FieldTester)
        assert mixed.fields['field'] is FirstMixin.field
        assert mixed.fields['field_a'] is FieldTester.field_a

    def test_duplicate_mixins(self):
        singly_mixed = self.mixologist.mix(FieldTester)
        doubly_mixed = self.mixologist.mix(singly_mixed)
        assert singly_mixed is doubly_mixed
        assert FieldTester is singly_mixed.unmixed_class

    def test_multiply_mixed(self):
        mixalot = Mixologist([ThirdMixin, FirstMixin])

        pre_mixed = mixalot.mix(self.mixologist.mix(FieldTester))
        post_mixed = self.mixologist.mix(mixalot.mix(FieldTester))

        assert pre_mixed.fields['field'] is FirstMixin.field
        assert post_mixed.fields['field'] is ThirdMixin.field

        assert FieldTester is pre_mixed.unmixed_class
        assert FieldTester is post_mixed.unmixed_class

        assert len(pre_mixed.__bases__) == 4  # 1 for the original class + 3 mixin classes
        assert len(post_mixed.__bases__) == 4


@XBlock.needs("i18n", "no_such_service")
@XBlock.wants("secret_service", "another_not_service")
class XBlockWithServices(XBlock):
    """
    Test XBlock class with service declarations.
    """
    def student_view(self, _context):
        """Try out some services."""
        # i18n is available, and works.
        def assert_equals_unicode(str1, str2):
            """`str1` equals `str2`, and both are Unicode strings."""
            assert str1 == str2
            assert isinstance(str1, six.text_type)
            assert isinstance(str2, six.text_type)

        i18n = self.runtime.service(self, "i18n")
        assert_equals_unicode("Welcome!", i18n.ugettext("Welcome!"))

        assert_equals_unicode("Plural", i18n.ungettext("Singular", "Plural", 0))
        assert_equals_unicode("Singular", i18n.ungettext("Singular", "Plural", 1))
        assert_equals_unicode("Plural", i18n.ungettext("Singular", "Plural", 2))

        when = datetime(2013, 2, 14, 22, 30, 17)
        assert_equals_unicode("2013-02-14", i18n.strftime(when, "%Y-%m-%d"))
        assert_equals_unicode("Feb 14, 2013", i18n.strftime(when, "SHORT_DATE"))
        assert_equals_unicode("Thursday, February 14, 2013", i18n.strftime(when, "LONG_DATE"))
        assert_equals_unicode("Feb 14, 2013 at 22:30", i18n.strftime(when, "DATE_TIME"))
        assert_equals_unicode("10:30:17 PM", i18n.strftime(when, "TIME"))

        # secret_service is available.
        assert self.runtime.service(self, "secret_service") == 17

        # no_such_service is not available, and raises an exception, because we
        # said we needed it.
        with pytest.raises(NoSuchServiceError, match="is not available"):
            self.runtime.service(self, "no_such_service")

        # another_not_service is not available, and returns None, because we
        # didn't need it, we only wanted it.
        assert self.runtime.service(self, "another_not_service") is None
        return Fragment()


def test_service():
    runtime = TestRuntime(services={
        'secret_service': 17,
        'field-data': DictFieldData({}),
    })
    block_type = 'test'
    def_id = runtime.id_generator.create_definition(block_type)
    usage_id = runtime.id_generator.create_usage(def_id)
    tester = XBlockWithServices(runtime, scope_ids=ScopeIds('user', block_type, def_id, usage_id))

    # Call the student_view to run its assertions.
    runtime.render(tester, 'student_view')


def test_ugettext_calls():
    """
    Test ugettext calls in xblock.
    """
    runtime = TestRuntime()
    block = XBlockWithServices(runtime, scope_ids=Mock(spec=[]))
    assert block.ugettext('test') == 'test'
    assert isinstance(block.ugettext('test'), six.text_type)

    # NoSuchServiceError exception should raise if i18n is none/empty.
    runtime = TestRuntime(services={
        'i18n': None
    })
    block = XBlockWithServices(runtime, scope_ids=Mock(spec=[]))
    with pytest.raises(NoSuchServiceError):
        block.ugettext('test')


@XBlock.needs("no_such_service_sub")
@XBlock.wants("another_not_service_sub")
class SubXBlockWithServices(XBlockWithServices):
    """
    Test that subclasses can use services declared on the parent.
    """
    def student_view(self, context):
        """Try the services."""
        # First, call the super class, its assertions should still pass.
        super(SubXBlockWithServices, self).student_view(context)

        # no_such_service_sub is not available, and raises an exception,
        # because we said we needed it.
        with pytest.raises(NoSuchServiceError, match="is not available"):
            self.runtime.service(self, "no_such_service_sub")

        # another_not_service_sub is not available, and returns None,
        # because we didn't need it, we only wanted it.
        assert self.runtime.service(self, "another_not_service_sub") is None
        return Fragment()


def test_sub_service():
    runtime = TestRuntime(id_reader=Mock(), services={
        'secret_service': 17,
        'field-data': DictFieldData({}),
    })
    tester = SubXBlockWithServices(runtime, scope_ids=Mock(spec=ScopeIds))

    # Call the student_view to run its assertions.
    runtime.render(tester, 'student_view')


class TestRuntimeGetBlock(TestCase):
    """
    Test the get_block default method on Runtime.
    """
    def setUp(self):
        patcher = patch.object(TestRuntime, 'construct_xblock')
        self.construct_block = patcher.start()
        self.addCleanup(patcher.stop)

        self.id_reader = Mock(IdReader)
        self.user_id = Mock()
        self.field_data = Mock(FieldData)
        self.runtime = TestRuntime(self.id_reader, services={'field-data': self.field_data})
        self.runtime.user_id = self.user_id

        self.usage_id = 'usage_id'

        # Can only get a definition id from the id_reader
        self.def_id = self.id_reader.get_definition_id.return_value

        # Can only get a block type from the id_reader
        self.block_type = self.id_reader.get_block_type.return_value

    def test_basic(self):
        self.runtime.get_block(self.usage_id)

        self.id_reader.get_definition_id.assert_called_with(self.usage_id)
        self.id_reader.get_block_type.assert_called_with(self.def_id)
        self.construct_block.assert_called_with(
            self.block_type,
            ScopeIds(self.user_id, self.block_type, self.def_id, self.usage_id),
            for_parent=None,
        )

    def test_missing_usage(self):
        self.id_reader.get_definition_id.side_effect = NoSuchUsage
        with self.assertRaises(NoSuchUsage):
            self.runtime.get_block(self.usage_id)

    def test_missing_definition(self):
        self.id_reader.get_block_type.side_effect = NoSuchDefinition

        # If we don't have a definition, then the usage doesn't exist
        with self.assertRaises(NoSuchUsage):
            self.runtime.get_block(self.usage_id)


class TestRuntimeDeprecation(WarningTestMixin, TestCase):
    """
    Tests to make sure that deprecated Runtime apis stay usable,
    but raise warnings.
    """

    def test_passed_field_data(self):
        field_data = Mock(spec=FieldData)
        with self.assertWarns(FieldDataDeprecationWarning):
            runtime = TestRuntime(Mock(spec=IdReader), field_data)
        with self.assertWarns(FieldDataDeprecationWarning):
            self.assertEqual(runtime.field_data, field_data)

    def test_set_field_data(self):
        field_data = Mock(spec=FieldData)
        runtime = TestRuntime(Mock(spec=IdReader), None)
        with self.assertWarns(FieldDataDeprecationWarning):
            runtime.field_data = field_data
        with self.assertWarns(FieldDataDeprecationWarning):
            self.assertEqual(runtime.field_data, field_data)
