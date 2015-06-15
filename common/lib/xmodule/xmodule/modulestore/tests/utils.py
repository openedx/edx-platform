"""
Helper classes and methods for running modulestore tests without Django.
"""
from importlib import import_module
from opaque_keys.edx.keys import UsageKey
from unittest import TestCase
from xblock.fields import XBlockMixin
from xmodule.x_module import XModuleMixin
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mixed import MixedModuleStore
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
        user_service=None,
        signal_handler=None,
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
        signal_handler=signal_handler,
        **options
    )


def mock_tab_from_json(tab_dict):
    """
    Mocks out the CourseTab.from_json to just return the tab_dict itself so that we don't have to deal
    with plugin errors.
    """
    return tab_dict


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
        'xblock_mixins': (EditInfoMixin, InheritanceMixin, LocationMixin, XModuleMixin),
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


class ProceduralCourseTestMixin(object):
    """
    Contains methods for testing courses generated procedurally
    """
    def populate_course(self, branching=2):
        """
        Add k chapters, k^2 sections, k^3 verticals, k^4 problems to self.course (where k = branching)
        """
        user_id = self.user.id
        self.populated_usage_keys = {}  # pylint: disable=attribute-defined-outside-init

        def descend(parent, stack):  # pylint: disable=missing-docstring
            if not stack:
                return

            xblock_type = stack[0]
            for _ in range(branching):
                child = ItemFactory.create(
                    category=xblock_type,
                    parent_location=parent.location,
                    user_id=user_id
                )
                self.populated_usage_keys.setdefault(xblock_type, []).append(
                    child.location
                )
                descend(child, stack[1:])

        descend(self.course, ['chapter', 'sequential', 'vertical', 'problem'])
