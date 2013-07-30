
import copy
from uuid import uuid4
from django.test import TestCase

from django.conf import settings
import xmodule.modulestore.django
from unittest.util import safe_repr


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

    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.mongo.draft.DraftModuleStore',
            'OPTIONS': modulestore_options
        },
        'direct': {
            'ENGINE': 'xmodule.modulestore.mongo.MongoModuleStore',
            'OPTIONS': modulestore_options
        }
    }


def xml_store_config(data_dir):
    """
    Defines default module store using XMLModuleStore.
    """
    return {
        'default': {
            'ENGINE': 'xmodule.modulestore.xml.XMLModuleStore',
            'OPTIONS': {
                'data_dir': data_dir,
                'default_class': 'xmodule.hidden_module.HiddenDescriptor',
            }
        }
    }


class ModuleStoreTestCase(TestCase):
    """ Subclass for any test case that uses the mongodb
    module store. This populates a uniquely named modulestore
    collection with templates before running the TestCase
    and drops it they are finished. """

    @staticmethod
    def update_course(course, data):
        """
        Updates the version of course in the modulestore
        with the metadata in 'data' and returns the updated version.

        'course' is an instance of CourseDescriptor for which we want
        to update metadata.

        'data' is a dictionary with an entry for each CourseField we want to update.
        """
        store = xmodule.modulestore.django.modulestore()
        store.update_metadata(course.location, data)
        updated_course = store.get_instance(course.id, course.location)
        return updated_course

    @staticmethod
    def flush_mongo_except_templates():
        """
        Delete everything in the module store except templates.
        """
        modulestore = xmodule.modulestore.django.modulestore()

        # This query means: every item in the collection
        # that is not a template
        query = {"_id.course": {"$ne": "templates"}}

        # Remove everything except templates
        modulestore.collection.remove(query)
        modulestore.collection.drop()

    @classmethod
    def setUpClass(cls):
        """
        Flush the mongo store and set up templates.
        """

        # Use a uuid to differentiate
        # the mongo collections on jenkins.
        cls.orig_modulestore = copy.deepcopy(settings.MODULESTORE)
        if 'direct' not in settings.MODULESTORE:
            settings.MODULESTORE['direct'] = settings.MODULESTORE['default']

        settings.MODULESTORE['default']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        settings.MODULESTORE['direct']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        xmodule.modulestore.django._MODULESTORES.clear()

        print settings.MODULESTORE

        TestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        """
        Revert to the old modulestore settings.
        """

        # Clean up by dropping the collection
        modulestore = xmodule.modulestore.django.modulestore()
        modulestore.collection.drop()

        xmodule.modulestore.django._MODULESTORES.clear()

        # Restore the original modulestore settings
        settings.MODULESTORE = cls.orig_modulestore

    def _pre_setup(self):
        """
        Remove everything but the templates before each test.
        """

        # Flush anything that is not a template
        ModuleStoreTestCase.flush_mongo_except_templates()

        # Call superclass implementation
        super(ModuleStoreTestCase, self)._pre_setup()

    def _post_teardown(self):
        """
        Flush everything we created except the templates.
        """
        # Flush anything that is not a template
        ModuleStoreTestCase.flush_mongo_except_templates()

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
