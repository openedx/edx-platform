from xmodule.x_module import XModuleFields
from xblock.core import Scope, String, Object
from xmodule.fields import Date, StringyInteger, NON_EDITABLE_SETTINGS_SCOPE
from xmodule.mako_module import  MakoModuleDescriptor
import unittest
from . import test_system
from mock import Mock


class TestFields(object):
    # Will be returned by editable_metadata_fields because Scope.settings.
    max_attempts = StringyInteger(scope=Scope.settings)
    # Will not be returned by editable_metadata_fields because declared as non-editable Scope.settings.
    due = Date(scope=NON_EDITABLE_SETTINGS_SCOPE)
    # Will not be returned by editable_metadata_fields because is not Scope.settings.
    student_answers = Object(scope=Scope.user_state)
    # Will be returned, and can override the inherited value from XModule.
    display_name = String(scope=Scope.settings)


class EditableMetadataFieldsTest(unittest.TestCase):

    def test_display_name_field(self):
        editable_fields = self.get_mako_editable_fields({})
        # Tests that the xblock fields (currently tags and name) get filtered out.
        self.assertEqual(1, len(editable_fields), "Expected only 1 editable field for mako descriptor.")
        self.assert_display_name_default(editable_fields)

    def test_override_default(self):
        # Tests that is_default is correct when a value overrides the default.
        editable_fields = self.get_mako_editable_fields({'display_name': 'foo'})
        display_name = editable_fields['display_name']
        self.assertFalse(display_name['is_default'])
        self.assertEqual('foo', display_name['value'])

    def test_additional_field(self):
        editable_fields = self.get_module_editable_fields({'max_attempts' : '7'})
        self.assertEqual(2, len(editable_fields))
        self.assert_field_values(editable_fields, 'max_attempts', TestFields.max_attempts, False, False, 7)
        self.assert_display_name_default(editable_fields)

        editable_fields = self.get_module_editable_fields({})
        self.assert_field_values(editable_fields, 'max_attempts', TestFields.max_attempts, True, False, None)

    def test_inherited_field(self):
        editable_fields = self.get_module_editable_fields({'display_name' : 'inherited'})
        self.assert_field_values(editable_fields, 'display_name', XModuleFields.display_name, False, True, 'inherited')

    # Start of helper methods
    def get_mako_editable_fields(self, model_data):
        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        return MakoModuleDescriptor(system=system, location=None, model_data=model_data).editable_metadata_fields

    def get_module_editable_fields(self, model_data):
        class TestModuleDescriptor(TestFields, MakoModuleDescriptor):
            pass

        system = test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        descriptor = TestModuleDescriptor(system=system, location=None, model_data=model_data)
        descriptor._inherited_metadata = {'display_name' : 'inherited'}
        return descriptor.editable_metadata_fields

    def assert_display_name_default(self, editable_fields):
        self.assert_field_values(editable_fields, 'display_name', XModuleFields.display_name, True, False, None)

    def assert_field_values(self, editable_fields, name, field, is_default, is_inherited, value):
        test_field = editable_fields[name]
        self.assertEqual(field, test_field['field'])
        self.assertEqual(is_default, test_field['is_default'])
        self.assertEqual(is_inherited, test_field['is_inherited'])
        self.assertEqual(value, test_field['value'])
