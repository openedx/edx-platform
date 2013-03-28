'''
Utilities for contentstore tests
'''

#pylint: disable=W0603

import json
import copy
from uuid import uuid4
from django.test import TestCase
from django.conf import settings

from student.models import Registration
from django.contrib.auth.models import User

import xmodule.modulestore.django
from xmodule.templates import update_templates

# Share modulestore setup between classes
# We need to use global variables, because
# each ModuleStoreTestCase subclass will have its
# own class variables, and we want to re-use the
# same modulestore for all test cases.

#pylint: disable=C0103
test_modulestore = None
#pylint: disable=C0103
orig_modulestore = None


class ModuleStoreTestCase(TestCase):
    """ Subclass for any test case that uses the mongodb
    module store. This populates a uniquely named modulestore
    collection with templates before running the TestCase
    and drops it they are finished. """

    @staticmethod
    def flush_mongo_except_templates():
        '''
        Delete everything in the module store except templates
        '''
        modulestore = xmodule.modulestore.django.modulestore()

        # This query means: every item in the collection
        # that is not a template
        query = { "_id.course": { "$ne": "templates" }}

        # Remove everything except templates
        modulestore.collection.remove(query)

    @staticmethod
    def load_templates_if_necessary():
        '''
        Load templates into the modulestore only if they do not already exist.
        We need the templates, because they are copied to create
        XModules such as sections and problems
        '''
        modulestore = xmodule.modulestore.django.modulestore()

        # Count the number of templates
        query = { "_id.course": "templates"}
        num_templates = modulestore.collection.find(query).count()

        if num_templates < 1:
            update_templates()

    @classmethod
    def setUpClass(cls):
        '''
        Flush the mongo store and set up templates
        '''
        global test_modulestore
        global orig_modulestore

        # Use a uuid to differentiate
        # the mongo collections on jenkins.
        if test_modulestore is None:
            orig_modulestore = copy.deepcopy(settings.MODULESTORE)
            test_modulestore = orig_modulestore
            test_modulestore['default']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
            test_modulestore['direct']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
            xmodule.modulestore.django._MODULESTORES = {}

        settings.MODULESTORE = test_modulestore

        TestCase.setUpClass()

    @classmethod
    def tearDownClass(cls):
        '''
        Revert to the old modulestore settings
        '''
        settings.MODULESTORE = orig_modulestore

    def _pre_setup(self):
        '''
        Remove everything but the templates before each test
        '''

        # Flush anything that is not a template
        ModuleStoreTestCase.flush_mongo_except_templates()

        # Check that we have templates loaded; if not, load them
        ModuleStoreTestCase.load_templates_if_necessary()

        # Call superclass implementation
        TestCase._pre_setup(self)

    def _post_teardown(self):
        '''
        Flush everything we created except the templates
        '''
        # Flush anything that is not a template
        ModuleStoreTestCase.flush_mongo_except_templates()

        # Call superclass implementation
        TestCase._post_teardown(self)



def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)


def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)


def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)
