"""
Modulestore configuration for test cases.
"""

from uuid import uuid4
from django.test import TestCase
from xmodule.modulestore.django import editable_modulestore, \
    clear_existing_modulestores


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
    mongo_config = mongo_store_config(data_dir)
    xml_config = xml_store_config(data_dir)

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mixed.MixedModuleStore',
            'OPTIONS': {
                'mappings': mappings,
                'stores': {
                    'default': mongo_config['default'],
                    'xml': xml_config['default']
                }
            }
        }
    }
    store['direct'] = store['default']
    return store


def mongo_store_config(data_dir):
    """
    Defines default module store using MongoModuleStore.

    Use of this config requires mongo to be running.
    """
    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'fs_root': data_dir,
                'render_template': 'edxmako.shortcuts.render_to_string'
            }
        }
    }

    store['direct'] = store['default']
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
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': {
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
            },
            'OPTIONS': modulestore_options
        }
    }

    store['direct'] = store['default']
    return store


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }

    store['direct'] = store['default']
    return store


def studio_store_config(data_dir):
    """
    Defines modulestore structure used by Studio tests.
    """
    store_config = {
        'host': 'localhost',
        'db': 'test_xmodule',
        'collection': 'modulestore{0}'.format(uuid4().hex[:5]),
    }
    options = {
        'default_class': 'xmodule.raw_module.RawDescriptor',
        'fs_root': data_dir,
        'render_template': 'edxmako.shortcuts.render_to_string',
    }

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': store_config,
            'OPTIONS': options
        },
        'direct': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'DOC_STORE_CONFIG': store_config,
            'OPTIONS': options
        },
        'draft': {
            'ENGINE': 'xmodule.modulestore.draft.DraftModuleStore',
            'DOC_STORE_CONFIG': store_config,
            'OPTIONS': options
        },
        'split': {
            'ENGINE': 'xmodule.modulestore.split_mongo.SplitMongoModuleStore',
            'DOC_STORE_CONFIG': store_config,
            'OPTIONS': options
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
    def update_course(course, data):
        """
        Updates the version of course in the modulestore
        with the metadata in 'data' and returns the updated version.

        'course' is an instance of CourseDescriptor for which we want
        to update metadata.

        'data' is a dictionary with an entry for each CourseField we want to update.
        """
        store = editable_modulestore('direct')
        store.update_metadata(course.location, data)
        updated_course = store.get_instance(course.id, course.location)
        return updated_course

    @staticmethod
    def drop_mongo_collection():
        """
        If using a Mongo-backed modulestore, drop the collection.
        """

        # This will return the mongo-backed modulestore
        # even if we're using a mixed modulestore
        store = editable_modulestore()

        if hasattr(store, 'collection'):
            store.collection.drop()

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
        cls.drop_mongo_collection()

        # Clear out the existing modulestores,
        # which will cause them to be re-created
        # the next time they are accessed.
        # We do this at *both* setup and teardown just to be safe.
        clear_existing_modulestores()

        TestCase.tearDownClass()

    def _pre_setup(self):
        """
        Flush the ModuleStore before each test.
        """

        # Flush the Mongo modulestore
        ModuleStoreTestCase.drop_mongo_collection()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Flush the ModuleStore after each test.
        """
        ModuleStoreTestCase.drop_mongo_collection()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._post_teardown()
