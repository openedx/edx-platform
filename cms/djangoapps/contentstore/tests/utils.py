from django.test import TestCase
import json

from student.models import Registration
from django.contrib.auth.models import User

import xmodule.modulestore.django
from xmodule.templates import update_templates

# Subclass TestCase and use to initialize the contentstore
class ModuleStoreTestCase(TestCase):
    """ Subclass for any test case that uses the mongodb 
    module store. This clears it out before running the TestCase
    and reinitilizes it with the templates afterwards. """

    def _pre_setup(self):
        super(ModuleStoreTestCase, self)._pre_setup()        
        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        update_templates()

    def _post_teardown(self):
        # Make sure you flush out the test modulestore after the end
        # of the last test so the collection will be deleted.
        # Otherwise there will be lingering collections leftover
        # from executing the tests.
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        super(ModuleStoreTestCase, self)._post_teardown()

def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)

def user(email):
    """look up a user by email"""
    return User.objects.get(email=email)

def registration(email):
    """look up registration object by email"""
    return Registration.objects.get(user__email=email)
