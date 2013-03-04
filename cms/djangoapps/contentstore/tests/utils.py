import json
import copy
from uuid import uuid4
from django.test import TestCase
from django.conf import settings

from student.models import Registration
from django.contrib.auth.models import User

import xmodule.modulestore.django
from xmodule.templates import update_templates


class ModuleStoreTestCase(TestCase):
    """ Subclass for any test case that uses the mongodb
    module store. This populates a uniquely named modulestore
    collection with templates before running the TestCase
    and drops it they are finished. """

    def _pre_setup(self):
        super(ModuleStoreTestCase, self)._pre_setup()

        # Use a uuid to differentiate
        # the mongo collections on jenkins.
        self.orig_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
        self.test_MODULESTORE = self.orig_MODULESTORE
        self.test_MODULESTORE['default']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        self.test_MODULESTORE['direct']['OPTIONS']['collection'] = 'modulestore_%s' % uuid4().hex
        settings.MODULESTORE = self.test_MODULESTORE

        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        update_templates()

    def _post_teardown(self):
        # Make sure you flush out the modulestore.
        # Drop the collection at the end of the test,
        # otherwise there will be lingering collections leftover
        # from executing the tests.
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        settings.MODULESTORE = self.orig_MODULESTORE

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
