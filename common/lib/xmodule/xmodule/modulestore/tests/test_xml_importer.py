"""
Tests for XML importer.
"""
import mock
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xblock.fields import String, Scope, ScopeIds, List
from xblock.runtime import Runtime, KvsFieldData, DictKeyValueStore
from xmodule.x_module import XModuleMixin
from opaque_keys.edx.locations import Location
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.xml_importer import _update_and_import_module, _update_module_location
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.tests import DATA_DIR
from uuid import uuid4
import unittest
import importlib


class ModuleStoreNoSettings(unittest.TestCase):
    """
    A mixin to create a mongo modulestore that avoids settings
    """
    HOST = MONGO_HOST
    PORT = MONGO_PORT_NUM
    DB = 'test_mongo_%s' % uuid4().hex[:5]
    COLLECTION = 'modulestore'
    FS_ROOT = DATA_DIR
    DEFAULT_CLASS = 'xmodule.modulestore.tests.test_xml_importer.StubXBlock'
    RENDER_TEMPLATE = lambda t_n, d, ctx=None, nsp='main': ''

    modulestore_options = {
        'default_class': DEFAULT_CLASS,
        'fs_root': DATA_DIR,
        'render_template': RENDER_TEMPLATE,
    }
    DOC_STORE_CONFIG = {
        'host': HOST,
        'port': PORT,
        'db': DB,
        'collection': COLLECTION,
    }
    MODULESTORE = {
        'ENGINE': 'xmodule.modulestore.mongo.DraftMongoModuleStore',
        'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
        'OPTIONS': modulestore_options
    }

    modulestore = None

    def cleanup_modulestore(self):
        """
        cleanup
        """
        if self.modulestore:
            self.modulestore._drop_database()  # pylint: disable=protected-access

    def setUp(self):
        """
        Add cleanups
        """
        self.addCleanup(self.cleanup_modulestore)
        super(ModuleStoreNoSettings, self).setUp()


#===========================================
def modulestore():
    """
    Mock the django dependent global modulestore function to disentangle tests from django
    """
    def load_function(engine_path):
        """
        Load the given engine
        """
        module_path, _, name = engine_path.rpartition('.')
        return getattr(importlib.import_module(module_path), name)

    if ModuleStoreNoSettings.modulestore is None:
        class_ = load_function(ModuleStoreNoSettings.MODULESTORE['ENGINE'])

        options = {}

        options.update(ModuleStoreNoSettings.MODULESTORE['OPTIONS'])
        options['render_template'] = render_to_template_mock

        # pylint: disable=star-args
        ModuleStoreNoSettings.modulestore = class_(
            None,  # contentstore
            ModuleStoreNoSettings.MODULESTORE['DOC_STORE_CONFIG'],
            branch_setting_func=lambda: ModuleStoreEnum.Branch.draft_preferred,
            **options
        )

    return ModuleStoreNoSettings.modulestore


# pylint: disable=unused-argument
def render_to_template_mock(*args):
    pass


class StubXBlock(XModuleMixin, InheritanceMixin):
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


class RemapNamespaceTest(ModuleStoreNoSettings):
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
        super(RemapNamespaceTest, self).setUp()

    def test_remap_namespace_native_xblock(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")

        # Explicitly set the content and settings fields
        self.xblock.test_content_field = "Explicitly set"
        self.xblock.test_settings_field = "Explicitly set"
        self.xblock.save()

        # Move to different runtime w/ different course id
        target_location_namespace = SlashSeparatedCourseKey("org", "course", "run")
        new_version = _update_and_import_module(
            self.xblock,
            modulestore(),
            999,
            self.xblock.location.course_key,
            target_location_namespace,
            do_import_static=False
        )

        # Check the XBlock's location
        self.assertEqual(new_version.location.course_key, target_location_namespace)

        # Check the values of the fields.
        # The content and settings fields should be preserved
        self.assertEqual(new_version.test_content_field, 'Explicitly set')
        self.assertEqual(new_version.test_settings_field, 'Explicitly set')

        # Expect that these fields are marked explicitly set
        self.assertIn(
            'test_content_field',
            new_version.get_explicitly_set_fields_by_scope(scope=Scope.content)
        )
        self.assertIn(
            'test_settings_field',
            new_version.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )

    def test_remap_namespace_native_xblock_default_values(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")

        # Do NOT set any values, so the fields should use the defaults
        self.xblock.save()

        # Remap the namespace
        target_location_namespace = Location("org", "course", "run", "category", "stubxblock")
        new_version = _update_and_import_module(
            self.xblock,
            modulestore(),
            999,
            self.xblock.location.course_key,
            target_location_namespace.course_key,
            do_import_static=False
        )

        # Check the values of the fields.
        # The content and settings fields should be the default values
        self.assertEqual(new_version.test_content_field, 'default value')
        self.assertEqual(new_version.test_settings_field, 'default value')

        # The fields should NOT appear in the explicitly set fields
        self.assertNotIn(
            'test_content_field',
            new_version.get_explicitly_set_fields_by_scope(scope=Scope.content)
        )
        self.assertNotIn(
            'test_settings_field',
            new_version.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )

    def test_remap_namespace_native_xblock_inherited_values(self):

        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")
        self.xblock.save()

        # Remap the namespace
        target_location_namespace = Location("org", "course", "run", "category", "stubxblock")
        new_version = _update_and_import_module(
            self.xblock,
            modulestore(),
            999,
            self.xblock.location.course_key,
            target_location_namespace.course_key,
            do_import_static=False
        )

        # Inherited fields should NOT be explicitly set
        self.assertNotIn(
            'start', new_version.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )
        self.assertNotIn(
            'graded', new_version.get_explicitly_set_fields_by_scope(scope=Scope.settings)
        )


class StubXBlockWithMutableFields(StubXBlock):
    """
    Stub XBlock used for testing mutable fields and children
    """
    has_children = True

    test_mutable_content_field = List(
        help="A mutable content field that will be explicitly set",
        scope=Scope.content,
    )

    test_mutable_settings_field = List(
        help="A mutable settings field that will be explicitly set",
        scope=Scope.settings,
    )


class UpdateLocationTest(ModuleStoreNoSettings):
    """
    Test that updating location preserves "is_set_on" status on fields
    """
    CONTENT_FIELDS = ['test_content_field', 'test_mutable_content_field']
    SETTINGS_FIELDS = ['test_settings_field', 'test_mutable_settings_field']
    CHILDREN_FIELDS = ['children']

    def setUp(self):
        """
        Create a stub XBlock backed by in-memory storage.
        """
        self.runtime = mock.MagicMock(Runtime)
        self.field_data = KvsFieldData(kvs=DictKeyValueStore())
        self.scope_ids = ScopeIds('Bob', 'mutablestubxblock', '123', 'import')
        self.xblock = StubXBlockWithMutableFields(self.runtime, self.field_data, self.scope_ids)

        self.fake_children_locations = [
            BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'mutablestubxblock', 'child1'),
            BlockUsageLocator(CourseLocator('org', 'course', 'run'), 'mutablestubxblock', 'child2'),
        ]

        super(UpdateLocationTest, self).setUp()

    def _check_explicitly_set(self, block, scope, expected_explicitly_set_fields, should_be_set=False):
        """ Gets fields that are explicitly set on block and checks if they are marked as explicitly set or not """
        actual_explicitly_set_fields = block.get_explicitly_set_fields_by_scope(scope=scope)
        assertion = self.assertIn if should_be_set else self.assertNotIn
        for field in expected_explicitly_set_fields:
            assertion(field, actual_explicitly_set_fields)

    def test_update_locations_native_xblock(self):
        """ Update locations updates location and keeps values and "is_set_on" status """
        # Set the XBlock's location
        self.xblock.location = Location("org", "import", "run", "category", "stubxblock")

        # Explicitly set the content, settings and children fields
        self.xblock.test_content_field = 'Explicitly set'
        self.xblock.test_settings_field = 'Explicitly set'
        self.xblock.test_mutable_content_field = [1, 2, 3]
        self.xblock.test_mutable_settings_field = ["a", "s", "d"]
        self.xblock.children = self.fake_children_locations  # pylint:disable=attribute-defined-outside-init
        self.xblock.save()

        # Update location
        target_location = self.xblock.location.replace(revision='draft')
        _update_module_location(self.xblock, target_location)
        new_version = self.xblock  # _update_module_location updates in-place

        # Check the XBlock's location
        self.assertEqual(new_version.location, target_location)

        # Check the values of the fields.
        # The content, settings and children fields should be preserved
        self.assertEqual(new_version.test_content_field, 'Explicitly set')
        self.assertEqual(new_version.test_settings_field, 'Explicitly set')
        self.assertEqual(new_version.test_mutable_content_field, [1, 2, 3])
        self.assertEqual(new_version.test_mutable_settings_field, ["a", "s", "d"])
        self.assertEqual(new_version.children, self.fake_children_locations)

        # Expect that these fields are marked explicitly set
        self._check_explicitly_set(new_version, Scope.content, self.CONTENT_FIELDS, should_be_set=True)
        self._check_explicitly_set(new_version, Scope.settings, self.SETTINGS_FIELDS, should_be_set=True)
        self._check_explicitly_set(new_version, Scope.children, self.CHILDREN_FIELDS, should_be_set=True)

        # Expect these fields pass "is_set_on" test
        for field in self.CONTENT_FIELDS + self.SETTINGS_FIELDS + self.CHILDREN_FIELDS:
            self.assertTrue(new_version.fields[field].is_set_on(new_version))
