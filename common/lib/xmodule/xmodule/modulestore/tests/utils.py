"""
Helper classes and methods for running modulestore tests without Django.
"""
from importlib import import_module
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import BlockUsageLocator
from unittest import TestCase
from xblock.fields import XBlockMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mixed import MixedModuleStore
from xmodule.modulestore.models import Block, CourseStructure
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.tests import DATA_DIR


def load_function(path):
    """
    Load a function by name.

    path is a string of the form "path.to.module.function"
    returns the imported python object `function` from `path.to.module`
    """
    module_path, _, name = path.rpartition('.')
    return getattr(import_module(module_path), name)


# pylint: disable=unused-argument
def create_modulestore_instance(
        engine,
        contentstore,
        doc_store_config,
        options,
        i18n_service=None,
        fs_service=None,
        user_service=None
):
    """
    This will return a new instance of a modulestore given an engine and options
    """
    class_ = load_function(engine)

    if issubclass(class_, ModuleStoreDraftAndPublished):
        options['branch_setting_func'] = lambda: ModuleStoreEnum.Branch.draft_preferred

    return class_(
        doc_store_config=doc_store_config,
        contentstore=contentstore,
        **options
    )


class LocationMixin(XBlockMixin):
    """
    Adds a `location` property to an :class:`XBlock` so it is more compatible
    with old-style :class:`XModule` API. This is a simplified version of
    :class:`XModuleMixin`.
    """
    @property
    def location(self):
        """ Get the UsageKey of this block. """
        return self.scope_ids.usage_id

    @location.setter
    def location(self, value):
        """ Set the UsageKey of this block. """
        assert isinstance(value, UsageKey)
        self.scope_ids = self.scope_ids._replace(  # pylint: disable=attribute-defined-outside-init,protected-access
            def_id=value,
            usage_id=value,
        )


class MixedSplitTestCase(TestCase):
    """
    Stripped-down version of ModuleStoreTestCase that can be used without Django
    (i.e. for testing in common/lib/ ). Sets up MixedModuleStore and Split.
    """
    RENDER_TEMPLATE = lambda t_n, d, ctx=None, nsp='main': u'{}: {}, {}'.format(t_n, repr(d), repr(ctx))
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': DATA_DIR,
        'render_template': RENDER_TEMPLATE,
        'xblock_mixins': (EditInfoMixin, InheritanceMixin, LocationMixin),
    }
    DOC_STORE_CONFIG = {
        'host': MONGO_HOST,
        'port': MONGO_PORT_NUM,
        'db': 'test_mongo_libs',
        'collection': 'modulestore',
        'asset_collection': 'assetstore',
    }
    MIXED_OPTIONS = {
        'stores': [
            {
                'NAME': 'split',
                'ENGINE': 'xmodule.modulestore.split_mongo.split_draft.DraftVersioningModuleStore',
                'DOC_STORE_CONFIG': DOC_STORE_CONFIG,
                'OPTIONS': modulestore_options
            },
        ]
    }

    def setUp(self):
        """
        Set up requirements for testing: a user ID and a modulestore
        """
        super(MixedSplitTestCase, self).setUp()
        self.user_id = ModuleStoreEnum.UserID.test

        self.store = MixedModuleStore(
            None,
            create_modulestore_instance=create_modulestore_instance,
            mappings={},
            **self.MIXED_OPTIONS
        )
        self.addCleanup(self.store.close_all_connections)
        self.addCleanup(self.store._drop_database)  # pylint: disable=protected-access

    def make_block(self, category, parent_block, **kwargs):
        """
        Create a block of type `category` as a child of `parent_block`, in any
        course or library. You can pass any field values as kwargs.
        """
        extra = {"publish_item": False, "user_id": self.user_id}
        extra.update(kwargs)
        return ItemFactory.create(
            category=category,
            parent=parent_block,
            parent_location=parent_block.location,
            modulestore=self.store,
            **extra
        )


class CourseStructureTestMixin(object):
    """
    Mixin used to help test implementations of implementation of ModuleStoreRead.get_course_structure.
    """
    def _add_item_to_structure(self, modulestore, locator, structure):
        item = modulestore.get_item(locator)
        locator_string = unicode(locator)
        block = {
            u'id': locator_string,
            u'block_type': item.category,
            u'display_name': item.display_name or item.name,
            u'format': getattr(item, 'format', None),
            u'graded': getattr(item, 'graded', False),
            u'children': []
        }

        if item.has_children:
            block[u'children'] = [unicode(child) for child in item.children]

        structure[locator_string] = Block.from_dict(block)

        if item.has_children:
            for child in item.children:
                self._add_item_to_structure(modulestore, child, structure)

    def _get_course_version(self, course_key, modulestore):  # pylint: disable=unused-argument
        return modulestore.get_branch_setting()

    def assertValidCourseStructure(self, course_key, modulestore):
        """
        Verifies that the course structure returned by a module store is valid.
        """
        actual = modulestore.get_course_structure(course_key)

        course = modulestore.get_course(course_key, depth=None)
        course_locator_string = unicode(BlockUsageLocator(course_key, 'course', course.scope_ids.usage_id.block_id))
        blocks = {
            course_locator_string: Block.from_dict({
                u'id': course_locator_string,
                u'block_type': u'course',
                u'display_name': course.display_name,
                u'format': None,
                u'graded': False,
                u'children': [unicode(child) for child in course.children]
            })
        }

        for child in course.children:
            self._add_item_to_structure(modulestore, child, blocks)

        expected = CourseStructure(course_locator_string, blocks,
                                   version=self._get_course_version(course_key, modulestore))
        self.assertEqual(actual, expected)
