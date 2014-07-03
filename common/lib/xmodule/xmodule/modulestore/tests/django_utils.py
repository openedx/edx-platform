"""
Modulestore configuration for test cases.
"""

from uuid import uuid4
from django.test import TestCase
from xmodule.modulestore.django import (
    modulestore, clear_existing_modulestores, loc_mapper)
from xmodule.modulestore import ModuleStoreEnum


def mixed_store_config(data_dir, mappings):
    """
    Return a `MixedModuleStore` configuration, which provides
    access to both Mongo- and XML-backed courses.

    `data_dir` is the directory from which to load XML-backed courses.
    `mappings` is a dictionary mapping course IDs to modulestores, for example:

        {
            'MITx/2.01x/2013_Spring': 'xml',
            'edx/999/2013_Spring': 'default'
        }

    where 'xml' and 'default' are the two options provided by this configuration,
    mapping (respectively) to XML-backed and Mongo-backed modulestores..
    """
    draft_mongo_config = draft_mongo_store_config(data_dir)
    xml_config = xml_store_config(data_dir)

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
            'OPTIONS': {
                'mappings': mappings,
                'stores': [
                    draft_mongo_config['default'],
                    xml_config['default']
                ]
            }
        }
    }
    return store


def draft_mongo_store_config(data_dir):
    """
    Defines default module store using DraftMongoModuleStore.
    """

    modulestore_options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string'
    }

    store = {
        'default': {
            'NAME': 'draft',
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    return store


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    store = {
        'default': {
            'NAME': 'xml',
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

    return store


class ModuleStoreTestCase(TestCase):
    """
    Subclass for any test case that uses a ModuleStore.
    Ensures that the ModuleStore is cleaned before/after each test.

    Usage:

        1. Create a subclass of `ModuleStoreTestCase`
        2. Use Django's @override_settings decorator to use
           the desired modulestore configuration.

           For example:

               MIXED_CONFIG = mixed_store_config(data_dir, mappings)

               @override_settings(MODULESTORE=MIXED_CONFIG)
               class FooTest(ModuleStoreTestCase):
                   # ...

        3. Use factories (e.g. `CourseFactory`, `ItemFactory`) to populate
           the modulestore with test data.

    NOTE:
        * For Mongo-backed courses (created with `CourseFactory`),
          the state of the course will be reset before/after each
          test method executes.

        * For XML-backed courses, the course state will NOT
          reset between test methods (although it will reset
          between test classes)

          The reason is: XML courses are not editable, so to reset
          a course you have to reload it from disk, which is slow.

          If you do need to reset an XML course, use
          `clear_existing_modulestores()` directly in
          your `setUp()` method.
    """

    @staticmethod
    def update_course(course):
        """
        Updates the version of course in the modulestore

        'course' is an instance of CourseDescriptor for which we want
        to update metadata.
        """
        store = modulestore()
        store.update_item(course, '**replace_user**')
        updated_course = store.get_course(course.id)
        return updated_course

    @staticmethod
    def drop_mongo_collections(modulestore_type=ModuleStoreEnum.Type.mongo):
        """
        If using a Mongo-backed modulestore & contentstore, drop the collections.
        """
        store = modulestore()
        if hasattr(store, '_get_modulestore_by_type'):
            store = store._get_modulestore_by_type(modulestore_type)  # pylint: disable=W0212
        if hasattr(store, 'collection'):
            connection = store.collection.database.connection
            store.collection.drop()
            connection.close()
        elif hasattr(store, 'close_all_connections'):
            store.close_all_connections()
        elif hasattr(store, 'db'):
            connection = store.db.connection
            connection.drop_database(store.db.name)
            connection.close()

        if hasattr(store, 'contentstore'):
            store.contentstore.drop_database()

        location_mapper = loc_mapper()
        if location_mapper.db:
            location_mapper.location_map.drop()
            location_mapper.db.connection.close()

    @classmethod
    def setUpClass(cls):
        """
        Delete the existing modulestores, causing them to be reloaded.
        """
        # Clear out any existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        clear_existing_modulestores()
        TestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Drop the existing modulestores, causing them to be reloaded.
        Clean up any data stored in Mongo.
        """
        # Clean up by flushing the Mongo modulestore
        cls.drop_mongo_collections()

        # Clear out the existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        # We do this at *both* setup and teardown just to be safe.
        clear_existing_modulestores()

        TestCase.tearDownClass()

    def _pre_setup(self):
        """
        Flush the ModuleStore.
        """

        # Flush the Mongo modulestore
        ModuleStoreTestCase.drop_mongo_collections()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Flush the ModuleStore after each test.
        """
        ModuleStoreTestCase.drop_mongo_collections()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._post_teardown()
