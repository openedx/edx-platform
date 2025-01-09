# disable missing docstring
# pylint: disable=missing-docstring


import unittest
from unittest.mock import Mock
import dateutil.parser

from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.field_data import DictFieldData
from xblock.fields import Any, Boolean, Dict, Float, Integer, List, Scope, String
from xblock.runtime import DictKeyValueStore, KvsFieldData

from xmodule.course_block import CourseBlock
from xmodule.fields import Date, RelativeTime, Timedelta
from xmodule.modulestore.inheritance import InheritanceKeyValueStore, InheritableFieldsMixin, InheritingFieldData
from xmodule.modulestore.split_mongo.split_mongo_kvs import SplitMongoKVS
from xmodule.seq_block import SequenceBlock
from xmodule.tests import get_test_descriptor_system
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml.factories import CourseFactory, ProblemFactory, SequenceFactory
from xmodule.x_module import XModuleMixin
from xmodule.xml_block import XmlMixin, deserialize_field, serialize_field


class CrazyJsonString(String):
    def to_json(self, value):
        return value + " JSON"


class TestFields:
    # Will be returned by editable_metadata_fields.
    max_attempts = Integer(scope=Scope.settings, default=1000, values={'min': 1, 'max': 10})
    # Will not be returned by editable_metadata_fields because filtered out by non_editable_metadata_fields.
    due = Date(scope=Scope.settings)
    # Will not be returned by editable_metadata_fields because is not Scope.settings.
    student_answers = Dict(scope=Scope.user_state)
    # Will be returned, and can override the inherited value from XModule.
    display_name = String(
        scope=Scope.settings,
        default='local default',
        display_name='Local Display Name',
        help='local help'
    )
    # Used for testing select type, effect of to_json method
    string_select = CrazyJsonString(
        scope=Scope.settings,
        default='default value',
        values=[{'display_name': 'first', 'value': 'value a'},
                {'display_name': 'second', 'value': 'value b'}]
    )
    showanswer = InheritableFieldsMixin.showanswer
    # Used for testing select type
    float_select = Float(scope=Scope.settings, default=.999, values=[1.23, 0.98])
    # Used for testing float type
    float_non_select = Float(scope=Scope.settings, default=.999, values={'min': 0, 'step': .3})
    # Used for testing that Booleans get mapped to select type
    boolean_select = Boolean(scope=Scope.settings)
    # Used for testing Lists
    list_field = List(scope=Scope.settings, default=[])


class InheritingFieldDataTest(unittest.TestCase):
    """
    Tests of InheritingFieldData.
    """

    class TestableInheritingXBlock(XmlMixin):  # lint-amnesty, pylint: disable=abstract-method
        """
        An XBlock we can use in these tests.
        """
        inherited = String(scope=Scope.settings, default="the default")
        not_inherited = String(scope=Scope.settings, default="nothing")

    def setUp(self):
        super().setUp()
        self.dummy_course_key = CourseLocator('test_org', 'test_123', 'test_run')
        self.system = get_test_descriptor_system()
        self.all_blocks = {}
        self.system.get_block = self.all_blocks.get
        self.field_data = InheritingFieldData(
            inheritable_names=['inherited'],
            kvs=DictKeyValueStore({}),
        )

    def get_block_using_split_kvs(self, block_type, block_id, fields, defaults):
        """
        Construct an Xblock with split mongo kvs.
        """
        kvs = SplitMongoKVS(
            definition=Mock(),
            initial_values=fields,
            default_values=defaults,
            parent=None
        )
        self.field_data = InheritingFieldData(
            inheritable_names=['inherited'],
            kvs=kvs,
        )
        block = self.get_a_block(
            usage_id=self.get_usage_id(block_type, block_id)
        )

        return block

    def get_a_block(self, usage_id=None):
        """
        Construct an XBlock for testing with.
        """
        scope_ids = Mock()
        if usage_id is None:
            block_id = f"_auto{len(self.all_blocks)}"
            usage_id = self.get_usage_id("course", block_id)
        scope_ids.usage_id = usage_id
        block = self.system.construct_xblock_from_class(
            self.TestableInheritingXBlock,
            field_data=self.field_data,
            scope_ids=scope_ids,
        )
        self.all_blocks[usage_id] = block
        return block

    def get_usage_id(self, block_type, block_id):
        """
        Constructs usage id using 'block_type' and 'block_id'
        """
        return BlockUsageLocator(self.dummy_course_key, block_type=block_type, block_id=block_id)

    def test_default_value(self):
        """
        Test that the Blocks with nothing set with return the fields' defaults.
        """
        block = self.get_a_block()
        assert block.inherited == 'the default'
        assert block.not_inherited == 'nothing'

    def test_set_value(self):
        """
        Test that If you set a value, that's what you get back.
        """
        block = self.get_a_block()
        block.inherited = "Changed!"
        block.not_inherited = "New Value!"
        assert block.inherited == 'Changed!'
        assert block.not_inherited == 'New Value!'

    def test_inherited(self):
        """
        Test that a child with get a value inherited from the parent.
        """
        parent_block = self.get_a_block(usage_id=self.get_usage_id("course", "parent"))
        parent_block.inherited = "Changed!"
        assert parent_block.inherited == 'Changed!'

        child = self.get_a_block(usage_id=self.get_usage_id("vertical", "child"))
        child.parent = parent_block.location
        assert child.inherited == 'Changed!'

    def test_inherited_across_generations(self):
        """
        Test that a child with get a value inherited from a great-grandparent.
        """
        parent = self.get_a_block(usage_id=self.get_usage_id("course", "parent"))
        parent.inherited = "Changed!"
        assert parent.inherited == 'Changed!'
        for child_num in range(10):
            usage_id = self.get_usage_id("vertical", f"child_{child_num}")
            child = self.get_a_block(usage_id=usage_id)
            child.parent = parent.location
            assert child.inherited == 'Changed!'

    def test_not_inherited(self):
        """
        Test that the fields not in the inherited_names list won't be inherited.
        """
        parent = self.get_a_block(usage_id=self.get_usage_id("course", "parent"))
        parent.not_inherited = "Changed!"
        assert parent.not_inherited == 'Changed!'

        child = self.get_a_block(usage_id=self.get_usage_id("vertical", "child"))
        child.parent = parent.location
        assert child.not_inherited == 'nothing'

    def test_non_defaults_inherited_across_lib(self):
        """
        Test that a child inheriting from library_content block, inherits fields
        from parent if these fields are not in its defaults.
        """
        parent_block = self.get_block_using_split_kvs(
            block_type="library_content",
            block_id="parent",
            fields=dict(inherited="changed!"),
            defaults=dict(inherited="parent's default"),
        )
        assert parent_block.inherited == 'changed!'

        child = self.get_block_using_split_kvs(
            block_type="problem",
            block_id="child",
            fields={},
            defaults={},
        )
        child.parent = parent_block.location
        assert child.inherited == 'changed!'

    def test_defaults_not_inherited_across_lib(self):
        """
        Test that a child inheriting from library_content block, does not inherit
        fields from parent if these fields are in its defaults already.
        """
        parent_block = self.get_block_using_split_kvs(
            block_type="library_content",
            block_id="parent",
            fields=dict(inherited="changed!"),
            defaults=dict(inherited="parent's default"),
        )
        assert parent_block.inherited == 'changed!'

        child = self.get_block_using_split_kvs(
            block_type="library_content",
            block_id="parent",
            fields={},
            defaults=dict(inherited="child's default"),
        )
        child.parent = parent_block.location
        assert child.inherited == "child's default"


class EditableMetadataFieldsTest(unittest.TestCase):
    class TestableXmlXBlock(XmlMixin, XModuleMixin):  # lint-amnesty, pylint: disable=abstract-method
        """
        This is subclassing `XModuleMixin` to use metadata fields in the unmixed class.
        """

    def test_display_name_field(self):
        editable_fields = self.get_xml_editable_fields(DictFieldData({}))
        # Tests that the xblock fields (currently tags and name) get filtered out.
        # Also tests that xml_attributes is filtered out of XmlMixin.
        assert 1 == len(editable_fields), editable_fields
        self.assert_field_values(
            editable_fields, 'display_name', XModuleMixin.display_name,
            explicitly_set=False, value=None, default_value=None
        )

    def test_override_default(self):
        # Tests that explicitly_set is correct when a value overrides the default (not inheritable).
        editable_fields = self.get_xml_editable_fields(DictFieldData({'display_name': 'foo'}))
        self.assert_field_values(
            editable_fields, 'display_name', XModuleMixin.display_name,
            explicitly_set=True, value='foo', default_value=None
        )

    def test_integer_field(self):
        block = self.get_block(DictFieldData({'max_attempts': '7'}))
        editable_fields = block.editable_metadata_fields
        assert 8 == len(editable_fields)
        self.assert_field_values(
            editable_fields, 'max_attempts', TestFields.max_attempts,
            explicitly_set=True, value=7, default_value=1000, type='Integer',
            options=TestFields.max_attempts.values
        )
        self.assert_field_values(
            editable_fields, 'display_name', TestFields.display_name,
            explicitly_set=False, value='local default', default_value='local default'
        )

        editable_fields = self.get_block(DictFieldData({})).editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'max_attempts', TestFields.max_attempts,
            explicitly_set=False, value=1000, default_value=1000, type='Integer',
            options=TestFields.max_attempts.values
        )

    def test_inherited_field(self):
        kvs = InheritanceKeyValueStore(initial_values={}, inherited_settings={'showanswer': 'inherited'})
        model_data = KvsFieldData(kvs)
        block = self.get_block(model_data)
        editable_fields = block.editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'showanswer', InheritableFieldsMixin.showanswer,
            explicitly_set=False, value='inherited', default_value='inherited'
        )

        # Mimic the case where display_name WOULD have been inherited, except we explicitly set it.
        kvs = InheritanceKeyValueStore(
            initial_values={'showanswer': 'explicit'},
            inherited_settings={'showanswer': 'inheritable value'}
        )
        model_data = KvsFieldData(kvs)
        block = self.get_block(model_data)
        editable_fields = block.editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'showanswer', InheritableFieldsMixin.showanswer,
            explicitly_set=True, value='explicit', default_value='inheritable value'
        )

    def test_type_and_options(self):
        # test_display_name_field verifies that a String field is of type "Generic".
        # test_integer_field verifies that a Integer field is of type "Integer".

        block = self.get_block(DictFieldData({}))
        editable_fields = block.editable_metadata_fields

        # Tests for select
        self.assert_field_values(
            editable_fields, 'string_select', TestFields.string_select,
            explicitly_set=False, value='default value', default_value='default value',
            type='Select', options=[{'display_name': 'first', 'value': 'value a JSON'},
                                    {'display_name': 'second', 'value': 'value b JSON'}]
        )

        self.assert_field_values(
            editable_fields, 'float_select', TestFields.float_select,
            explicitly_set=False, value=.999, default_value=.999,
            type='Select', options=[1.23, 0.98]
        )

        self.assert_field_values(
            editable_fields, 'boolean_select', TestFields.boolean_select,
            explicitly_set=False, value=None, default_value=None,
            type='Select', options=[{'display_name': "True", "value": True}, {'display_name': "False", "value": False}]
        )

        # Test for float
        self.assert_field_values(
            editable_fields, 'float_non_select', TestFields.float_non_select,
            explicitly_set=False, value=.999, default_value=.999,
            type='Float', options={'min': 0, 'step': .3}
        )

        self.assert_field_values(
            editable_fields, 'list_field', TestFields.list_field,
            explicitly_set=False, value=[], default_value=[],
            type='List'
        )

    # Start of helper methods
    def get_xml_editable_fields(self, field_data):
        runtime = get_test_descriptor_system()
        return runtime.construct_xblock_from_class(
            self.TestableXmlXBlock,
            scope_ids=Mock(),
            field_data=field_data,
        ).editable_metadata_fields

    def get_block(self, field_data):
        class TestModuleBlock(TestFields, self.TestableXmlXBlock):  # lint-amnesty, pylint: disable=abstract-method
            @property
            def non_editable_metadata_fields(self):
                non_editable_fields = super().non_editable_metadata_fields
                non_editable_fields.append(TestModuleBlock.due)
                return non_editable_fields

        system = get_test_descriptor_system(render_template=Mock())
        return system.construct_xblock_from_class(TestModuleBlock, field_data=field_data, scope_ids=Mock())

    def assert_field_values(self, editable_fields, name, field, explicitly_set, value, default_value,  # lint-amnesty, pylint: disable=dangerous-default-value
                            type='Generic', options=[]):  # lint-amnesty, pylint: disable=redefined-builtin
        test_field = editable_fields[name]

        assert field.name == test_field['field_name']
        assert field.display_name == test_field['display_name']
        assert field.help == test_field['help']

        assert field.to_json(value) == test_field['value']
        assert field.to_json(default_value) == test_field['default_value']

        assert options == test_field['options']
        assert type == test_field['type']

        assert explicitly_set == test_field['explicitly_set']


class TestSerialize(unittest.TestCase):
    """ Tests the serialize, method, which is not dependent on type. """

    def test_serialize(self):
        assert serialize_field(None) == 'null'
        assert serialize_field(-2) == '-2'
        assert serialize_field('2') == '2'
        assert serialize_field(-3.41) == '-3.41'
        assert serialize_field('2.589') == '2.589'
        assert serialize_field(False) == 'false'
        assert serialize_field('false') == 'false'
        assert serialize_field('fAlse') == 'fAlse'
        assert serialize_field('hat box') == 'hat box'
        serialized_dict = serialize_field({'bar': 'hat', 'frog': 'green'})
        assert serialized_dict == '{"bar": "hat", "frog": "green"}' or serialized_dict == '{"frog": "green", "bar": "hat"}'  # lint-amnesty, pylint: disable=consider-using-in, line-too-long
        assert serialize_field([3.5, 5.6]) == '[3.5, 5.6]'
        assert serialize_field(['foo', 'bar']) == '["foo", "bar"]'
        assert serialize_field("2012-12-31T23:59:59Z") == '2012-12-31T23:59:59Z'
        assert serialize_field("1 day 12 hours 59 minutes 59 seconds") == '1 day 12 hours 59 minutes 59 seconds'
        assert serialize_field(dateutil.parser.parse('2012-12-31T23:59:59Z')) == '2012-12-31T23:59:59+00:00'


class TestDeserialize(unittest.TestCase):

    def assertDeserializeEqual(self, expected, arg):
        """
        Asserts the result of deserialize_field.
        """
        assert deserialize_field(self.field_type(), arg) == expected  # lint-amnesty, pylint: disable=no-member

    def assertDeserializeNonString(self):
        """
        Asserts input value is returned for None or something that is not a string.
        For all types, 'null' is also always returned as None.
        """
        self.assertDeserializeEqual(None, None)
        self.assertDeserializeEqual(3.14, 3.14)
        self.assertDeserializeEqual(True, True)
        self.assertDeserializeEqual([10], [10])
        self.assertDeserializeEqual({}, {})
        self.assertDeserializeEqual([], [])
        self.assertDeserializeEqual(None, 'null')


class TestDeserializeInteger(TestDeserialize):
    """ Tests deserialize as related to Integer type. """

    field_type = Integer

    def test_deserialize(self):
        self.assertDeserializeEqual(-2, '-2')
        self.assertDeserializeEqual("450", '"450"')

        # False can be parsed as a int (converts to 0)
        self.assertDeserializeEqual(False, 'false')
        # True can be parsed as a int (converts to 1)
        self.assertDeserializeEqual(True, 'true')
        # 2.78 can be converted to int, so the string will be deserialized
        self.assertDeserializeEqual(-2.78, '-2.78')

    def test_deserialize_unsupported_types(self):
        self.assertDeserializeEqual('[3]', '[3]')
        # '2.78' cannot be converted to int, so input value is returned
        self.assertDeserializeEqual('"-2.78"', '"-2.78"')
        # 'false' cannot be converted to int, so input value is returned
        self.assertDeserializeEqual('"false"', '"false"')
        self.assertDeserializeNonString()


class TestDeserializeFloat(TestDeserialize):
    """ Tests deserialize as related to Float type. """

    field_type = Float

    def test_deserialize(self):
        self.assertDeserializeEqual(-2, '-2')
        self.assertDeserializeEqual("450", '"450"')
        self.assertDeserializeEqual(-2.78, '-2.78')
        self.assertDeserializeEqual("0.45", '"0.45"')

        # False can be parsed as a float (converts to 0)
        self.assertDeserializeEqual(False, 'false')
        # True can be parsed as a float (converts to 1)
        self.assertDeserializeEqual(True, 'true')

    def test_deserialize_unsupported_types(self):
        self.assertDeserializeEqual('[3]', '[3]')
        # 'false' cannot be converted to float, so input value is returned
        self.assertDeserializeEqual('"false"', '"false"')
        self.assertDeserializeNonString()


class TestDeserializeBoolean(TestDeserialize):
    """ Tests deserialize as related to Boolean type. """

    field_type = Boolean

    def test_deserialize(self):
        # json.loads converts the value to Python bool
        self.assertDeserializeEqual(False, 'false')
        self.assertDeserializeEqual(True, 'true')

        # json.loads fails, string value is returned.
        self.assertDeserializeEqual('False', 'False')
        self.assertDeserializeEqual('True', 'True')

        # json.loads deserializes as a string
        self.assertDeserializeEqual('false', '"false"')
        self.assertDeserializeEqual('fAlse', '"fAlse"')
        self.assertDeserializeEqual("TruE", '"TruE"')

        # 2.78 can be converted to a bool, so the string will be deserialized
        self.assertDeserializeEqual(-2.78, '-2.78')

        self.assertDeserializeNonString()


class TestDeserializeString(TestDeserialize):
    """ Tests deserialize as related to String type. """

    field_type = String

    def test_deserialize(self):
        self.assertDeserializeEqual('hAlf', '"hAlf"')
        self.assertDeserializeEqual('false', '"false"')
        self.assertDeserializeEqual('single quote', 'single quote')

    def test_deserialize_unsupported_types(self):
        self.assertDeserializeEqual('3.4', '3.4')
        self.assertDeserializeEqual('false', 'false')
        self.assertDeserializeEqual('2', '2')
        self.assertDeserializeEqual('[3]', '[3]')
        self.assertDeserializeNonString()


class TestDeserializeAny(TestDeserialize):
    """ Tests deserialize as related to Any type. """

    field_type = Any

    def test_deserialize(self):
        self.assertDeserializeEqual('hAlf', '"hAlf"')
        self.assertDeserializeEqual('false', '"false"')
        self.assertDeserializeEqual({'bar': 'hat', 'frog': 'green'}, '{"bar": "hat", "frog": "green"}')
        self.assertDeserializeEqual([3.5, 5.6], '[3.5, 5.6]')
        self.assertDeserializeEqual('[', '[')
        self.assertDeserializeEqual(False, 'false')
        self.assertDeserializeEqual(3.4, '3.4')
        self.assertDeserializeNonString()


class TestDeserializeList(TestDeserialize):
    """ Tests deserialize as related to List type. """

    field_type = List

    def test_deserialize(self):
        self.assertDeserializeEqual(['foo', 'bar'], '["foo", "bar"]')
        self.assertDeserializeEqual([3.5, 5.6], '[3.5, 5.6]')
        self.assertDeserializeEqual([], '[]')

    def test_deserialize_unsupported_types(self):
        self.assertDeserializeEqual('3.4', '3.4')
        self.assertDeserializeEqual('false', 'false')
        self.assertDeserializeEqual('2', '2')
        self.assertDeserializeNonString()


class TestDeserializeDate(TestDeserialize):
    """ Tests deserialize as related to Date type. """

    field_type = Date

    def test_deserialize(self):
        self.assertDeserializeEqual('2012-12-31T23:59:59Z', "2012-12-31T23:59:59Z")
        self.assertDeserializeEqual('2012-12-31T23:59:59Z', '"2012-12-31T23:59:59Z"')
        self.assertDeserializeNonString()


class TestDeserializeTimedelta(TestDeserialize):
    """ Tests deserialize as related to Timedelta type. """

    field_type = Timedelta

    def test_deserialize(self):
        self.assertDeserializeEqual(
            '1 day 12 hours 59 minutes 59 seconds',
            '1 day 12 hours 59 minutes 59 seconds'
        )
        self.assertDeserializeEqual(
            '1 day 12 hours 59 minutes 59 seconds',
            '"1 day 12 hours 59 minutes 59 seconds"'
        )
        self.assertDeserializeNonString()


class TestDeserializeRelativeTime(TestDeserialize):
    """ Tests deserialize as related to Timedelta type. """

    field_type = RelativeTime

    def test_deserialize(self):
        """
        There is no check for

        self.assertDeserializeEqual('10:20:30', '10:20:30')
        self.assertDeserializeNonString()

        because these two tests work only because json.loads fires exception,
        and xml_module.deserialized_field catches it and returns same value,
        so there is nothing field-specific here.
        But other modules do it, so I'm leaving this comment for PR reviewers.
        """

        # test that from_json produces no exceptions
        self.assertDeserializeEqual('10:20:30', '"10:20:30"')


class TestXmlAttributes(XModuleXmlImportTest):

    def test_unknown_attribute(self):
        assert not hasattr(CourseBlock, 'unknown_attr')
        course = self.process_xml(CourseFactory.build(unknown_attr='value'))
        assert not hasattr(course, 'unknown_attr')
        assert course.xml_attributes['unknown_attr'] == 'value'

    def test_known_attribute(self):
        assert hasattr(CourseBlock, 'show_calculator')
        course = self.process_xml(CourseFactory.build(show_calculator='true'))
        assert course.show_calculator
        assert 'show_calculator' not in course.xml_attributes

    def test_rerandomize_in_policy(self):
        # Rerandomize isn't a basic attribute of Sequence
        assert not hasattr(SequenceBlock, 'rerandomize')

        root = SequenceFactory.build(policy={'rerandomize': 'never'})
        ProblemFactory.build(parent=root)

        seq = self.process_xml(root)

        # Rerandomize is added to the constructed sequence via the InheritableFieldsMixin
        assert seq.rerandomize == 'never'

        # Rerandomize is a known value coming from policy, and shouldn't appear
        # in xml_attributes
        assert 'rerandomize' not in seq.xml_attributes

    def test_attempts_in_policy(self):
        # attempts isn't a basic attribute of Sequence
        assert not hasattr(SequenceBlock, 'attempts')

        root = SequenceFactory.build(policy={'attempts': '1'})
        ProblemFactory.build(parent=root)

        seq = self.process_xml(root)

        # attempts isn't added to the constructed sequence, because
        # it's not in the InheritableFieldsMixin
        assert not hasattr(seq, 'attempts')

        # attempts is an unknown attribute, so we should include it
        # in xml_attributes so that it gets written out (despite the misleading
        # name)
        assert 'attempts' in seq.xml_attributes

    def check_inheritable_attribute(self, attribute, value):
        # `attribute` isn't a basic attribute of Sequence
        assert not hasattr(SequenceBlock, attribute)

        # `attribute` is added by InheritableFieldsMixin
        assert hasattr(InheritableFieldsMixin, attribute)

        root = SequenceFactory.build(policy={attribute: str(value)})
        ProblemFactory.build(parent=root)

        # InheritableFieldsMixin will be used when processing the XML
        assert InheritableFieldsMixin in root.xblock_mixins

        seq = self.process_xml(root)

        assert seq.unmixed_class == SequenceBlock
        assert not seq.__class__ == SequenceBlock

        # `attribute` is added to the constructed sequence, because
        # it's in the InheritableFieldsMixin
        assert getattr(seq, attribute) == value

        # `attribute` is a known attribute, so we shouldn't include it
        # in xml_attributes
        assert attribute not in seq.xml_attributes

    def test_inheritable_attributes(self):
        self.check_inheritable_attribute('days_early_for_beta', 2)
        self.check_inheritable_attribute('max_attempts', 5)
        self.check_inheritable_attribute('visible_to_staff_only', True)
