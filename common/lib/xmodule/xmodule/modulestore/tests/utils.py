"""
Helper classes and methods for running modulestore tests without Django.
"""
from importlib import import_module
from unittest import TestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.draft_and_published import ModuleStoreDraftAndPublished
from xmodule.modulestore.edit_info import EditInfoMixin
from xmodule.modulestore.inheritance import InheritanceMixin
from xmodule.modulestore.mixed import MixedModuleStore
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
def create_modulestore_instance(engine, contentstore, doc_store_config, options, i18n_service=None, fs_service=None):
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


class MixedSplitTestCase(TestCase):
    """
    Stripped-down version of ModuleStoreTestCase that can be used without Django
    (i.e. for testing in common/lib/ ). Sets up MixedModuleStore and Split.
    """
    RENDER_TEMPLATE = lambda t_n, d, ctx = None, nsp = 'main': ''
    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': DATA_DIR,
        'render_template': RENDER_TEMPLATE,
        'xblock_mixins': (EditInfoMixin, InheritanceMixin),
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
