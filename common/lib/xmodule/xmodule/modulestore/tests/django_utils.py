import copy
from uuid import uuid4
from django.test import TestCase

from django.conf import settings
from xmodule.modulestore.django import modulestore, clear_existing_modulestores
from unittest.util import safe_repr


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
            'OPTIONS': {
                'default_class': 'xmodule.raw_module.RawDescriptor',
                'host': 'localhost',
                'db': 'test_xmodule',
                'collection': 'modulestore_%s' % uuid4().hex,
                'fs_root': data_dir,
                'render_template': 'mitxmako.shortcuts.render_to_string'
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
        'host': 'localhost',
        'db': 'test_xmodule',
        'collection': 'modulestore_%s' % uuid4().hex,
        'fs_root': data_dir,
        'render_template': 'mitxmako.shortcuts.render_to_string'
    }

    store = {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
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


class ModuleStoreTestCase(TestCase):
    """
    Subclass for any test case that uses a ModuleStore.

    Ensures that the ModuleStore is cleaned before/after each test.
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
        store = modulestore()
        store.update_metadata(course.location, data)
        updated_course = store.get_instance(course.id, course.location)
        return updated_course

    @staticmethod
    def drop_mongo_collection():
        """
        If using a Mongo-backed modulestore, drop the collection.
        """
        store = modulestore()

        if hasattr(store, 'collection'):
            store.collection.drop()

    @classmethod
    def setUpClass(cls):
        """
        Flush the ModuleStore.
        """

        # Use a uuid to differentiate
        # the mongo collections on jenkins.
        cls.orig_modulestore = copy.deepcopy(settings.MODULESTORE)
        if 'direct' not in settings.MODULESTORE:
            settings.MODULESTORE['direct'] = settings.MODULESTORE['default']

        settings.MODULESTORE['default']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        settings.MODULESTORE['direct']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        clear_existing_modulestores()

        print settings.MODULESTORE

        TestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Revert to the old modulestore settings.
        """

        # Clean up by dropping the collection
        cls.drop_mongo_collection()

        clear_existing_modulestores()

        # Restore the original modulestore settings
        settings.MODULESTORE = cls.orig_modulestore

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


    def assert2XX(self, status_code, msg=None):
        """
        Assert that the given value is a success status (between 200 and 299)
        """
        msg = self._formatMessage(msg, "%s is not a success status" % safe_repr(status_code))
        self.assertTrue(status_code >= 200 and status_code < 300, msg=msg)

    def assert3XX(self, status_code, msg=None):
        """
        Assert that the given value is a redirection status (between 300 and 399)
        """
        msg = self._formatMessage(msg, "%s is not a redirection status" % safe_repr(status_code))
        self.assertTrue(status_code >= 300 and status_code < 400, msg=msg)

    def assert4XX(self, status_code, msg=None):
        """
        Assert that the given value is a client error status (between 400 and 499)
        """
        msg = self._formatMessage(msg, "%s is not a client error status" % safe_repr(status_code))
        self.assertTrue(status_code >= 400 and status_code < 500, msg=msg)

    def assert5XX(self, status_code, msg=None):
        """
        Assert that the given value is a server error status (between 500 and 599)
        """
        msg = self._formatMessage(msg, "%s is not a server error status" % safe_repr(status_code))
        self.assertTrue(status_code >= 500 and status_code < 600, msg=msg)
