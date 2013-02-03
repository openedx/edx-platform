from django.test import TestCase
from xmodule.modulestore.django import modulestore, _MODULESTORES
from xmodule.templates import update_templates

# Subclass TestCase and use to initialize the contentstore
class CmsTestCase(TestCase):
    """ Subclass for any test case that uses the mongodb 
    module store. This clears it out before running the TestCase
    and reinitilizes it with the templates afterwards. """

    def _pre_setup(self):
        super(CmsTestCase, self)._pre_setup()        
        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        _MODULESTORES = {}
        modulestore().collection.drop()
        update_templates()

    def _post_teardown(self):
        # Make sure you flush out the test modulestore after the end
        # of the last test because otherwise on the next run
        # cms/djangoapps/contentstore/__init__.py
        # update_templates() will try to update the templates
        # via upsert and it sometimes seems to be messing things up.
        _MODULESTORES = {}
        modulestore().collection.drop()
        super(CmsTestCase, self)._post_teardown()