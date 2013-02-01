import json
import shutil
from django.test import TestCase
from django.test.client import Client
from override_settings import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from path import path
import json
from fs.osfs import OSFS
import copy
from mock import Mock

import xmodule.modulestore.django
from factories import *

# Subclass TestCase and use to initialize the contentstore
class CmsTestCase(TestCase):

    def _pre_setup(self):
        super(CmsTestCase, self)._pre_setup()        
        # Flush and initialize the module store
        # It needs the templates because it creates new records
        # by cloning from the template.
        # Note that if your test module gets in some weird state
        # (though it shouldn't), do this manually
        # from the bash shell to drop it:
        # $ mongo test_xmodule --eval "db.dropDatabase()"
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        xmodule.templates.update_templates()

    def _post_teardown(self):
        # Make sure you flush out the test modulestore after the end
        # of the last test because otherwise on the next run
        # cms/djangoapps/contentstore/__init__.py
        # update_templates() will try to update the templates
        # via upsert and it sometimes seems to be messing things up.
        xmodule.modulestore.django._MODULESTORES = {}
        xmodule.modulestore.django.modulestore().collection.drop()
        super(CmsTestCase, self)._post_teardown()        

def parse_json(response):
    """Parse response, which is assumed to be json"""
    return json.loads(response.content)

TEST_DATA_MODULESTORE = copy.deepcopy(settings.MODULESTORE)
TEST_DATA_MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
TEST_DATA_MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')

@override_settings(MODULESTORE=TEST_DATA_MODULESTORE)
class NewContentStoreTest(CmsTestCase):

    def setUp(self):
        # super(NewContentStoreTest, self).setUp()
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        # user = UserFactory(username=uname, email=email, password=password,
        #             is_staff=True, is_active=True)
        # user.is_authenticated= Mock(return_value=True)


        self.client = Client()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'template': 'i4x://edx/templates/course/Empty',
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            }

    def tearDown(self):
        # super(NewContentStoreTest, self).tearDown()
        pass

    def test_create_course(self):
        """Test new course creation - happy path"""
        resp = self.client.post(reverse('create_new_course'), self.course_data)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['id'], 'i4x://MITx/999/course/Robot_Super_Course')
