# disable missing docstring
#pylint: disable=C0111

from xmodule.x_module import XModuleFields
from xblock.core import Scope, String, Object, Boolean, Integer, Float
from xmodule.fields import Date
from xmodule.xml_module import XmlDescriptor
import unittest
from .import test_system
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
    student_answers = Object(scope=Scope.user_state)
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
