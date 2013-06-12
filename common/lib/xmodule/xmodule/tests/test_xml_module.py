# disable missing docstring
#pylint: disable=C0111

from xmodule.x_module import XModuleFields
from xblock.core import Scope, String, Dict, Boolean, Integer, Float, Any, List
from xmodule.fields import Date, Timedelta
from xmodule.xml_module import XmlDescriptor, serialize_field, deserialize_field
import unittest
from .import test_system
from nose.tools import assert_equals
from mock import Mock


class CrazyJsonString(String):
    def to_json(self, value):
        return value + " JSON"


class TestFields(object):
    # Will be returned by editable_metadata_fields.
    max_attempts = Integer(scope=Scope.settings, default=1000, values={'min': 1, 'max': 10})
    # Will not be returned by editable_metadata_fields because filtered out by non_editable_metadata_fields.
    due = Date(scope=Scope.settings)
    # Will not be returned by editable_metadata_fields because is not Scope.settings.
    student_answers = Dict(scope=Scope.user_state)
    # Will be returned, and can override the inherited value from XModule.
    display_name = String(scope=Scope.settings, default='local default', display_name='Local Display Name',
                          help='local help')
    # Used for testing select type, effect of to_json method
    string_select = CrazyJsonString(
        scope=Scope.settings,
        default='default value',
        values=[{'display_name': 'first', 'value': 'value a'},
                {'display_name': 'second', 'value': 'value b'}]
    )
    # Used for testing select type
    float_select = Float(scope=Scope.settings, default=.999, values=[1.23, 0.98])
    # Used for testing float type
    float_non_select = Float(scope=Scope.settings, default=.999, values={'min': 0, 'step': .3})
    # Used for testing that Booleans get mapped to select type
    boolean_select = Boolean(scope=Scope.settings)


class EditableMetadataFieldsTest(unittest.TestCase):
    def test_display_name_field(self):
        editable_fields = self.get_xml_editable_fields({})
        # Tests that the xblock fields (currently tags and name) get filtered out.
        # Also tests that xml_attributes is filtered out of XmlDescriptor.
        self.assertEqual(1, len(editable_fields), "Expected only 1 editable field for xml descriptor.")
        self.assert_field_values(
            editable_fields, 'display_name', XModuleFields.display_name,
            explicitly_set=False, inheritable=False, value=None, default_value=None
        )

    def test_override_default(self):
        # Tests that explicitly_set is correct when a value overrides the default (not inheritable).
        editable_fields = self.get_xml_editable_fields({'display_name': 'foo'})
        self.assert_field_values(
            editable_fields, 'display_name', XModuleFields.display_name,
            explicitly_set=True, inheritable=False, value='foo', default_value=None
        )

    def test_integer_field(self):
        descriptor = self.get_descriptor({'max_attempts': '7'})
        editable_fields = descriptor.editable_metadata_fields
        self.assertEqual(6, len(editable_fields))
        self.assert_field_values(
            editable_fields, 'max_attempts', TestFields.max_attempts,
            explicitly_set=True, inheritable=False, value=7, default_value=1000, type='Integer',
            options=TestFields.max_attempts.values
        )
        self.assert_field_values(
            editable_fields, 'display_name', TestFields.display_name,
            explicitly_set=False, inheritable=False, value='local default', default_value='local default'
        )

        editable_fields = self.get_descriptor({}).editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'max_attempts', TestFields.max_attempts,
            explicitly_set=False, inheritable=False, value=1000, default_value=1000, type='Integer',
            options=TestFields.max_attempts.values
        )

    def test_inherited_field(self):
        model_val = {'display_name': 'inherited'}
        descriptor = self.get_descriptor(model_val)
        # Mimic an inherited value for display_name (inherited and inheritable are the same in this case).
        descriptor._inherited_metadata = model_val
        descriptor._inheritable_metadata = model_val
        editable_fields = descriptor.editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'display_name', TestFields.display_name,
            explicitly_set=False, inheritable=True, value='inherited', default_value='inherited'
        )

        descriptor = self.get_descriptor({'display_name': 'explicit'})
        # Mimic the case where display_name WOULD have been inherited, except we explicitly set it.
        descriptor._inheritable_metadata = {'display_name': 'inheritable value'}
        descriptor._inherited_metadata = {}
        editable_fields = descriptor.editable_metadata_fields
        self.assert_field_values(
            editable_fields, 'display_name', TestFields.display_name,
            explicitly_set=True, inheritable=True, value='explicit', default_value='inheritable value'
        )

    def test_type_and_options(self):
        # test_display_name_field verifies that a String field is of type "Generic".
        # test_integer_field verifies that a StringyInteger field is of type "Integer".

        descriptor = self.get_descriptor({})
        editable_fields = descriptor.editable_metadata_fields

        # Tests for select
        self.assert_field_values(
            editable_fields, 'string_select', TestFields.string_select,
            explicitly_set=False, inheritable=False, value='default value', default_value='default value',
            type='Select', options=[{'display_name': 'first', 'value': 'value a JSON'},
                                    {'display_name': 'second', 'value': 'value b JSON'}]
        )

        self.assert_field_values(
            editable_fields, 'float_select', TestFields.float_select,
            explicitly_set=False, inheritable=False, value=.999, default_value=.999,
            type='Select', options=[1.23, 0.98]
        )

        self.assert_field_values(
            editable_fields, 'boolean_select', TestFields.boolean_select,
            explicitly_set=False, inheritable=False, value=None, default_value=None,
            type='Select', options=[{'display_name': "True", "value": True}, {'display_name': "False", "value": False}]
        )

        # Test for float
        self.assert_field_values(
            editable_fields, 'float_non_select', TestFields.float_non_select,
            explicitly_set=False, inheritable=False, value=.999, default_value=.999,
            type='Float', options={'min': 0, 'step': .3}
        )


    # Start of helper methods
    def get_xml_editable_fields(self, model_data):
        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        return XmlDescriptor(system=system, location=None, model_data=model_data).editable_metadata_fields

    def get_descriptor(self, model_data):
        class TestModuleDescriptor(TestFields, XmlDescriptor):
            @property
            def non_editable_metadata_fields(self):
                non_editable_fields = super(TestModuleDescriptor, self).non_editable_metadata_fields
                non_editable_fields.append(TestModuleDescriptor.due)
                return non_editable_fields

        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        return TestModuleDescriptor(system=system, location=None, model_data=model_data)

    def assert_field_values(self, editable_fields, name, field, explicitly_set, inheritable, value, default_value,
                            type='Generic', options=[]):
        test_field = editable_fields[name]

        self.assertEqual(field.name, test_field['field_name'])
        self.assertEqual(field.display_name, test_field['display_name'])
        self.assertEqual(field.help, test_field['help'])

        self.assertEqual(field.to_json(value), test_field['value'])
        self.assertEqual(field.to_json(default_value), test_field['default_value'])

        self.assertEqual(options, test_field['options'])
        self.assertEqual(type, test_field['type'])

        self.assertEqual(explicitly_set, test_field['explicitly_set'])
        self.assertEqual(inheritable, test_field['inheritable'])


def assertSerializeEqual(expected, arg):
    """
    Asserts the result of serialize_field.
    """
    assert_equals(expected, serialize_field(arg))


def assertDeserializeEqual(field, expected, arg):
    """
    Asserts the result of deserialize_field.
    """
    assert_equals(expected, deserialize_field(field, arg))


def assertDeserializeNonString(field):
    """
    Asserts input value is returned for None or something that is not a string.
    """
    assertDeserializeEqual(field, None, None)
    assertDeserializeEqual(field, 3.14, 3.14)
    assertDeserializeEqual(field, True, True)
    assertDeserializeEqual(field, [10], [10])
    assertDeserializeEqual(field, {}, {})
    assertDeserializeEqual(field, [], [])


class TestSerializeInteger(unittest.TestCase):
    """ Tests serialize/deserialize as related to Integer type. """

    def test_serialize(self):
        assertSerializeEqual('-2', -2)
        assertSerializeEqual('"2"', '2')
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Integer(), None, 'null')
        assertDeserializeEqual(Integer(), -2, '-2')
        assertDeserializeEqual(Integer(), "450", '"450"')

        # False can be parsed as a int (converts to 0)
        assertDeserializeEqual(Integer(), False, 'false')
        # True can be parsed as a int (converts to 1)
        assertDeserializeEqual(Integer(), True, 'true')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(Integer(), '[3]', '[3]')
        assertDeserializeNonString(Integer())


class FloatTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Float type. """

    def test_serialize(self):
        assertSerializeEqual('-2', -2)
        assertSerializeEqual('"2"', '2')
        assertSerializeEqual('-3.41', -3.41)
        assertSerializeEqual('"2.589"', '2.589')
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Float(), None, 'null')
        assertDeserializeEqual(Float(), -2, '-2')
        assertDeserializeEqual(Float(), "450", '"450"')
        assertDeserializeEqual(Float(), -2.78, '-2.78')
        assertDeserializeEqual(Float(), "0.45", '"0.45"')

        # False can be parsed as a float (converts to 0)
        assertDeserializeEqual(Float(), False, 'false')
        # True can be parsed as a float (converts to 1)
        assertDeserializeEqual(Float(), True, 'true')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(Float(), '[3]', '[3]')
        assertDeserializeNonString(Float())


class BooleanTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Boolean type. """

    def test_serialize(self):
        assertSerializeEqual('false', False)
        assertSerializeEqual('"false"', 'false')
        assertSerializeEqual('"fAlse"', 'fAlse')
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        # json.loads converts the value to Python bool
        assertDeserializeEqual(Boolean(), False, 'false')
        assertDeserializeEqual(Boolean(), True, 'true')

        # json.loads fails, string value is returned.
        assertDeserializeEqual(Boolean(), 'False', 'False')
        assertDeserializeEqual(Boolean(), 'True', 'True')

        # json.loads deserializes 'null' to None
        assertDeserializeEqual(Boolean(), None, 'null')

        # json.loads deserializes as a string
        assertDeserializeEqual(Boolean(), 'false', '"false"')
        assertDeserializeEqual(Boolean(), 'fAlse', '"fAlse"')
        assertDeserializeEqual(Boolean(), "TruE", '"TruE"')

        assertDeserializeNonString(Boolean())


class StringTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to String type. """

    def test_serialize(self):
        assertSerializeEqual('"hat box"', 'hat box')
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        assertDeserializeEqual(String(), 'hAlf', '"hAlf"')
        assertDeserializeEqual(String(), 'false', '"false"')
        assertDeserializeEqual(String(), 'single quote', 'single quote')
        assertDeserializeEqual(String(), None, 'null')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(String(), '3.4', '3.4')
        assertDeserializeEqual(String(), 'false', 'false')
        assertDeserializeEqual(String(), '2', '2')
        assertDeserializeEqual(String(), '[3]', '[3]')
        assertDeserializeNonString(String())


class AnyTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Any type. """

    def test_serialize(self):
        assertSerializeEqual('{"bar": "hat", "frog": "green"}', {'bar': 'hat', 'frog' : 'green'})
        assertSerializeEqual('[3.5, 5.6]', [3.5, 5.6])
        assertSerializeEqual('"hat box"', 'hat box')
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        assertDeserializeEqual(Any(), 'hAlf', '"hAlf"')
        assertDeserializeEqual(Any(), 'false', '"false"')
        assertDeserializeEqual(Any(), None, 'null')
        assertDeserializeEqual(Any(), {'bar': 'hat', 'frog' : 'green'}, '{"bar": "hat", "frog": "green"}')
        assertDeserializeEqual(Any(), [3.5, 5.6], '[3.5, 5.6]')
        assertDeserializeEqual(Any(), '[', '[')
        assertDeserializeEqual(Any(), False, 'false')
        assertDeserializeEqual(Any(), 3.4, '3.4')
        assertDeserializeNonString(Any())


class ListTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Any type. """

    def test_serialize(self):
        assertSerializeEqual('["foo", "bar"]', ['foo', 'bar'])
        assertSerializeEqual('[3.5, 5.6]', [3.5, 5.6])
        assertSerializeEqual('null', None)

    def test_deserialize(self):
        assertDeserializeEqual(List(), ['foo', 'bar'], '["foo", "bar"]')
        assertDeserializeEqual(List(), [3.5, 5.6], '[3.5, 5.6]')
        assertDeserializeEqual(List(), [], '[]')
        assertDeserializeEqual(List(), None, 'null')

    def test_deserialize_unsupported_types(self):
        assertDeserializeEqual(List(), '3.4', '3.4')
        assertDeserializeEqual(List(), 'false', 'false')
        assertDeserializeEqual(List(), '2', '2')
        assertDeserializeNonString(List())


class DateTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Date type. """

    def test_serialize(self):
        assertSerializeEqual('"2012-12-31T23:59:59Z"', "2012-12-31T23:59:59Z")

    def test_deserialize(self):
        assertDeserializeEqual(Date(), '2012-12-31T23:59:59Z', "2012-12-31T23:59:59Z")
        assertDeserializeEqual(Date(), '2012-12-31T23:59:59Z', '"2012-12-31T23:59:59Z"')
        assertDeserializeNonString(Date())


class TimedeltaTest(unittest.TestCase):
    """ Tests serialize/deserialize as related to Timedelta type. """

    def test_serialize(self):
        assertSerializeEqual('"1 day 12 hours 59 minutes 59 seconds"',
            "1 day 12 hours 59 minutes 59 seconds")

    def test_deserialize(self):
        assertDeserializeEqual(Timedelta(), '1 day 12 hours 59 minutes 59 seconds',
            '1 day 12 hours 59 minutes 59 seconds')
        assertDeserializeEqual(Timedelta(), '1 day 12 hours 59 minutes 59 seconds',
            '"1 day 12 hours 59 minutes 59 seconds"')
        assertDeserializeNonString(Timedelta())
