#pylint: disable=E1101

import json
import shutil
import sys
import mock
from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
from django.core.urlresolvers import reverse
from path import path
from tempdir import mkdtemp_clean
from fs.osfs import OSFS
import copy
from json import loads
from datetime import timedelta

from django.contrib.auth.models import User
from django.dispatch import Signal
from contentstore.utils import get_modulestore
from contentstore.tests.utils import parse_json

from auth.authz import add_user_to_creator_group

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from xmodule.modulestore import Location, mongo
from xmodule.modulestore.store_utilities import clone_course
from xmodule.modulestore.store_utilities import delete_course
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.xml_importer import import_from_xml, perform_xlint
from xmodule.modulestore.inheritance import own_metadata
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.utils import restore_asset_from_trashcan, empty_asset_trashcan

from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.seq_module import SequenceDescriptor
from xmodule.modulestore.exceptions import ItemNotFoundError

from contentstore.views.component import ADVANCED_COMPONENT_TYPES
from xmodule.exceptions import NotFoundError

from django_comment_common.utils import are_permissions_roles_seeded
from xmodule.exceptions import InvalidVersionError
import datetime
from pytz import UTC
from uuid import uuid4
from pymongo import MongoClient
from student.models import CourseEnrollment

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['OPTIONS']['db'] = 'test_xcontent_%s' % uuid4().hex


class MongoCollectionFindWrapper(object):
    def __init__(self, original):
        self.original = original
        self.counter = 0

    def find(self, query, *args, **kwargs):
        self.counter = self.counter + 1
        return self.original(query, *args, **kwargs)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ContentStoreImportNoStaticTest(ModuleStoreTestCase):
    """
    Tests that rely on the toy and test_import_course courses.
    TODO: refactor using CourseFactory so they do not.
    """
    def setUp(self):

        settings.MODULESTORE['default']['OPTIONS']['fs_root'] = path('common/test/data')
        settings.MODULESTORE['direct']['OPTIONS']['fs_root'] = path('common/test/data')
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

        # Save the data that we've just changed to the db.
        self.user.save()

        self.client = Client()
        self.client.login(username=uname, password=password)

    def load_test_import_course(self):
        '''
        Load the standard course used to test imports (for do_import_static=False behavior).  
        '''
        content_store = contentstore()
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['test_import_course'], static_content_store=content_store, do_import_static=False, verbose=True)
        course_location = CourseDescriptor.id_to_location('edX/test_import_course/2012_Fall')
        course = module_store.get_item(course_location)
        self.assertIsNotNone(course)

        return module_store, content_store, course, course_location


    def test_static_import(self):
        '''
        Stuff in static_import should always be imported into contentstore
        '''
        module_store, content_store, course, course_location = self.load_test_import_course()

        # make sure we have ONE asset in our contentstore ("should_be_imported.html")
        all_assets = content_store.get_all_content_for_course(course_location)
        print "len(all_assets)=%d" % len(all_assets)
        self.assertEqual(len(all_assets), 1)

        content = None
        try:
            location = StaticContent.get_location_from_path('/c4x/edX/test_import_course/asset/should_be_imported.html')
            content = content_store.find(location)
        except NotFoundError:
            pass

        self.assertIsNotNone(content)
        
        # make sure course.lms.static_asset_path is correct
        print "static_asset_path = {0}".format(course.lms.static_asset_path)
        self.assertEqual(course.lms.static_asset_path, 'test_import_course')


    def test_asset_import_nostatic(self):
        '''
        This test validates that an image asset is NOT imported when do_import_static=False
        '''
        content_store = contentstore()

        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store, do_import_static=False, verbose=True)

        course_location = CourseDescriptor.id_to_location('edX/toy/2012_Fall')
        course = module_store.get_item(course_location)

        # make sure we have NO assets in our contentstore
        all_assets = content_store.get_all_content_for_course(course_location)
        print "len(all_assets)=%d" % len(all_assets)
        self.assertEqual(len(all_assets), 0)


    def test_no_static_link_rewrites_on_import(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], do_import_static=False, verbose=True)

        handouts = module_store.get_item(Location(['i4x', 'edX', 'toy', 'course_info', 'handouts', None]))
        self.assertIn('/static/', handouts.data)

        handouts = module_store.get_item(Location(['i4x', 'edX', 'toy', 'html', 'toyhtml', None]))
        self.assertIn('/static/', handouts.data)

