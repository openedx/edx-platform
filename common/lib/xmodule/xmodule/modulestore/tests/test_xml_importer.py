"""
Tests for XML importer.
"""
from unittest import TestCase
import mock
from xblock.core import XBlock
from xblock.fields import String, Scope, ScopeIds
from xblock.runtime import Runtime, KvsFieldData, DictKeyValueStore
from xmodule.x_module import XModuleMixin
from xmodule.modulestore import Location
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.xml_importer import remap_namespace


class StubXBlock(XBlock, XModuleMixin, InheritanceMixin):
    """
    Stub XBlock used for testing.
    """
    test_content_field = String(
        help="A content field that will be explicitly set",
        scope=Scope.content,
        default="default value"
    )

    test_settings_field = String(
        help="A settings field that will be explicitly set",
        scope=Scope.settings,
        default="default value"
    )


class RemapNamespaceTest(TestCase):
    """
    Test that remapping the namespace from import to the actual course location.
    """

    def setUp(self):
        """
        Create a stub XBlock backed by in-memory storage.
        """
        self.runtime = mock.MagicMock(Runtime)
        self.field_data = KvsFieldData(kvs=DictKeyValueStore())
        self.scope_ids = ScopeIds('Bob', 'stubxblock', '123', 'import')
        self.xblock = StubXBlock(self.runtime, self.field_data, self.scope_ids)

    def test_remap_namespace_native_xblock(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")

        # Explicitly set the content and settings fields
        self.xblock.test_content_field = "Explicitly set"
        self.xblock.test_settings_field = "Explicitly set"
        self.xblock.save()

        # Remap the namespace
        target_location_namespace = Location("org", "course", "run", "category", "stubxblock")
        remap_namespace(self.xblock, target_location_namespace)

        # Check the XBlock's location
        self.assertEqual(self.xblock.location, target_location_namespace)

        # Check the values of the fields.
        # The content and settings fields should be preserved
        self.assertEqual(self.xblock.test_content_field, 'Explicitly set')
        self.assertEqual(self.xblock.test_settings_field, 'Explicitly set')

        # Expect that these fields are marked explicitly set
        self.assertIn(
            'test_content_field',
            self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.content)
        )
        self.assertIn(
            'test_settings_field',
            self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )

    def test_remap_namespace_native_xblock_default_values(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")

        # Do NOT set any values, so the fields should use the defaults
        self.xblock.save()

        # Remap the namespace
        target_location_namespace = Location("org", "course", "run", "category", "stubxblock")
        remap_namespace(self.xblock, target_location_namespace)

        # Check the values of the fields.
        # The content and settings fields should be the default values
        self.assertEqual(self.xblock.test_content_field, 'default value')
        self.assertEqual(self.xblock.test_settings_field, 'default value')

        # The fields should NOT appear in the explicitly set fields
        self.assertNotIn(
            'test_content_field',
            self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.content)
        )
        self.assertNotIn(
            'test_settings_field',
            self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )

    def test_remap_namespace_native_xblock_inherited_values(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")
        self.xblock.save()

        # Remap the namespace
        target_location_namespace = Location("org", "course", "run", "category", "stubxblock")
        remap_namespace(self.xblock, target_location_namespace)

        # Inherited fields should NOT be explicitly set
        self.assertNotIn(
            'start', self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )
        self.assertNotIn(
            'graded', self.xblock.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )

