"""
Helper classes and methods for running modulestore tests without Django.
"""
import random

from contextlib import contextmanager, nested
from importlib import import_module
from opaque_keys.edx.keys import UsageKey
from path import Path as path
from shutil import rmtree
from tempfile import mkdtemp
from unittest import TestCase

from xblock.fields import XBlockMixin
from xmodule.x_module import XModuleMixin
from xmodule.contentstore.mongo import MongoContentStore
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mixed import MixedModuleStore
from xmodule.modulestore.mongo.base import ModuleStoreEnum
from xmodule.modulestore.mongo.draft import DraftModuleStore
from xmodule.modulestore.split_mongo.split_draft import DraftVersioningModuleStore
from xmodule.modulestore.tests.factories import ItemFactory
from xmodule.modulestore.tests.mongo_connection import MONGO_PORT_NUM, MONGO_HOST
from xmodule.modulestore.xml import XMLModuleStore
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
        self.scope_ids = self.scope_ids._replace(
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
    def populate_course(self, branching=2, emit_signals=False):
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

        with self.store.bulk_operations(self.course.id, emit_signals=emit_signals):
            descend(self.course, ['chapter', 'sequential', 'vertical', 'problem'])


class MemoryCache(object):
    """
    This fits the metadata_inheritance_cache_subsystem interface used by
    the modulestore, and stores the data in a dictionary in memory.
    """
    def __init__(self):
        self._data = {}

    def get(self, key, default=None):
        """
        Get a key from the cache.

        Args:
            key: The key to update.
            default: The value to return if the key hasn't been set previously.
        """
        return self._data.get(key, default)

    def set(self, key, value):
        """
        Set a key in the cache.

        Args:
            key: The key to update.
            value: The value change the key to.
        """
        self._data[key] = value


class MongoContentstoreBuilder(object):
    """
    A builder class for a MongoContentStore.
    """
    @contextmanager
    def build(self):
        """
        A contextmanager that returns a MongoContentStore, and deletes its contents
        when the context closes.
        """
        contentstore = MongoContentStore(
            db='contentstore{}'.format(random.randint(0, 10000)),
            collection='content',
            **COMMON_DOCSTORE_CONFIG
        )
        contentstore.ensure_indexes()

        try:
            yield contentstore
        finally:
            # Delete the created database
            contentstore._drop_database()  # pylint: disable=protected-access

    def __repr__(self):
        return 'MongoContentstoreBuilder()'


class StoreBuilderBase(object):
    """
    Base class for all modulestore builders.
    """
    @contextmanager
    def build(self, **kwargs):
        """
        Build the modulstore, optionally building the contentstore as well.
        """
        contentstore = kwargs.pop('contentstore', None)
        if not contentstore:
            with self.build_without_contentstore() as (contentstore, modulestore):
                yield contentstore, modulestore
        else:
            with self.build_with_contentstore(contentstore) as modulestore:
                yield modulestore

    @contextmanager
    def build_without_contentstore(self):
        """
        Build both the contentstore and the modulestore.
        """
        with MongoContentstoreBuilder().build() as contentstore:
            with self.build_with_contentstore(contentstore) as modulestore:
                yield contentstore, modulestore


class MongoModulestoreBuilder(StoreBuilderBase):
    """
    A builder class for a DraftModuleStore.
    """
    @contextmanager
    def build_with_contentstore(self, contentstore):
        """
        A contextmanager that returns an isolated mongo modulestore, and then deletes
        all of its data at the end of the context.

        Args:
            contentstore: The contentstore that this modulestore should use to store
                all of its assets.
        """
        doc_store_config = dict(
            db='modulestore{}'.format(random.randint(0, 10000)),
            collection='xmodule',
            asset_collection='asset_metadata',
            **COMMON_DOCSTORE_CONFIG
        )

        # Set up a temp directory for storing filesystem content created during import
        fs_root = mkdtemp()

        modulestore = DraftModuleStore(
            contentstore,
            doc_store_config,
            fs_root,
            render_template=repr,
            branch_setting_func=lambda: ModuleStoreEnum.Branch.draft_preferred,
            metadata_inheritance_cache_subsystem=MemoryCache(),
            xblock_mixins=XBLOCK_MIXINS,
        )
        modulestore.ensure_indexes()

        try:
            yield modulestore
        finally:
            # Delete the created database
            modulestore._drop_database()  # pylint: disable=protected-access

            # Delete the created directory on the filesystem
            rmtree(fs_root, ignore_errors=True)

    def __repr__(self):
        return 'MongoModulestoreBuilder()'


class VersioningModulestoreBuilder(StoreBuilderBase):
    """
    A builder class for a VersioningModuleStore.
    """
    @contextmanager
    def build_with_contentstore(self, contentstore):
        """
        A contextmanager that returns an isolated versioning modulestore, and then deletes
        all of its data at the end of the context.

        Args:
            contentstore: The contentstore that this modulestore should use to store
                all of its assets.
        """
        doc_store_config = dict(
            db='modulestore{}'.format(random.randint(0, 10000)),
            collection='split_module',
            **COMMON_DOCSTORE_CONFIG
        )
        # Set up a temp directory for storing filesystem content created during import
        fs_root = mkdtemp()

        modulestore = DraftVersioningModuleStore(
            contentstore,
            doc_store_config,
            fs_root,
            render_template=repr,
            xblock_mixins=XBLOCK_MIXINS,
        )
        modulestore.ensure_indexes()

        try:
            yield modulestore
        finally:
            # Delete the created database
            modulestore._drop_database()  # pylint: disable=protected-access

            # Delete the created directory on the filesystem
            rmtree(fs_root, ignore_errors=True)

    def __repr__(self):
        return 'SplitModulestoreBuilder()'


class XmlModulestoreBuilder(StoreBuilderBase):
    """
    A builder class for a XMLModuleStore.
    """
    # pylint: disable=unused-argument
    @contextmanager
    def build_with_contentstore(self, contentstore=None, course_ids=None):
        """
        A contextmanager that returns an isolated xml modulestore

        Args:
            contentstore: The contentstore that this modulestore should use to store
                all of its assets.
        """
        modulestore = XMLModuleStore(
            DATA_DIR,
            course_ids=course_ids,
            default_class='xmodule.hidden_module.HiddenDescriptor',
            xblock_mixins=XBLOCK_MIXINS,
        )

        yield modulestore


class MixedModulestoreBuilder(StoreBuilderBase):
    """
    A builder class for a MixedModuleStore.
    """
    def __init__(self, store_builders, mappings=None):
        """
        Args:
            store_builders: A list of modulestore builder objects. These will be instantiated, in order,
                as the backing stores for the MixedModuleStore.
            mappings: Any course mappings to pass to the MixedModuleStore on instantiation.
        """
        self.store_builders = store_builders
        self.mappings = mappings or {}
        self.mixed_modulestore = None

    @contextmanager
    def build_with_contentstore(self, contentstore):
        """
        A contextmanager that returns a mixed modulestore built on top of modulestores
        generated by other builder classes.

        Args:
            contentstore: The contentstore that this modulestore should use to store
                all of its assets.
        """
        names, generators = zip(*self.store_builders)

        with nested(*(gen.build_with_contentstore(contentstore) for gen in generators)) as modulestores:
            # Make the modulestore creation function just return the already-created modulestores
            store_iterator = iter(modulestores)
            next_modulestore = lambda *args, **kwargs: store_iterator.next()

            # Generate a fake list of stores to give the already generated stores appropriate names
            stores = [{'NAME': name, 'ENGINE': 'This space deliberately left blank'} for name in names]

            self.mixed_modulestore = MixedModuleStore(
                contentstore,
                self.mappings,
                stores,
                create_modulestore_instance=next_modulestore,
                xblock_mixins=XBLOCK_MIXINS,
            )

            yield self.mixed_modulestore

    def __repr__(self):
        return 'MixedModulestoreBuilder({!r}, {!r})'.format(self.store_builders, self.mappings)

    def asset_collection(self):
        """
        Returns the collection storing the asset metadata.
        """
        all_stores = self.mixed_modulestore.modulestores
        if len(all_stores) > 1:
            return None

        store = all_stores[0]
        if hasattr(store, 'asset_collection'):
            # Mongo modulestore beneath mixed.
            # Returns the entire collection with *all* courses' asset metadata.
            return store.asset_collection
        else:
            # Split modulestore beneath mixed.
            # Split stores all asset metadata in the structure collection.
            return store.db_connection.structures


COMMON_DOCSTORE_CONFIG = {
    'host': MONGO_HOST,
    'port': MONGO_PORT_NUM,
}
DATA_DIR = path(__file__).dirname().parent.parent / "tests" / "data" / "xml-course-root"
TEST_DATA_DIR = 'common/test/data/'

XBLOCK_MIXINS = (InheritanceMixin, XModuleMixin)


MIXED_MODULESTORE_BOTH_SETUP = MixedModulestoreBuilder([
    ('draft', MongoModulestoreBuilder()),
    ('split', VersioningModulestoreBuilder())
])
DRAFT_MODULESTORE_SETUP = MixedModulestoreBuilder([('draft', MongoModulestoreBuilder())])
SPLIT_MODULESTORE_SETUP = MixedModulestoreBuilder([('split', VersioningModulestoreBuilder())])
MIXED_MODULESTORE_SETUPS = (
    DRAFT_MODULESTORE_SETUP,
    SPLIT_MODULESTORE_SETUP,
)
MIXED_MS_SETUPS_SHORT = (
    'mixed_mongo',
    'mixed_split',
)
DIRECT_MODULESTORE_SETUPS = (
    MongoModulestoreBuilder(),
    # VersioningModulestoreBuilder(),  # FUTUREDO: LMS-11227
)
DIRECT_MS_SETUPS_SHORT = (
    'mongo',
    #'split',
)
MODULESTORE_SETUPS = DIRECT_MODULESTORE_SETUPS + MIXED_MODULESTORE_SETUPS
MODULESTORE_SHORTNAMES = DIRECT_MS_SETUPS_SHORT + MIXED_MS_SETUPS_SHORT
SHORT_NAME_MAP = dict(zip(MODULESTORE_SETUPS, MODULESTORE_SHORTNAMES))

CONTENTSTORE_SETUPS = (MongoContentstoreBuilder(),)


class PureModulestoreTestCase(TestCase):
    """
    A TestCase designed to make testing Modulestore implementations without using Django
    easier.
    """

    MODULESTORE = None

    def setUp(self):
        super(PureModulestoreTestCase, self).setUp()

        builder = self.MODULESTORE.build()
        self.assets, self.store = builder.__enter__()
        self.addCleanup(builder.__exit__, None, None, None)
