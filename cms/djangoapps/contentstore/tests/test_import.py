#pylint: disable=E1101
"""
Tests for import_from_xml using the mongo modulestore.
"""

from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
from path import path
import copy

from django.contrib.auth.models import User

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.modulestore_config import TEST_MODULESTORE

from xmodule.modulestore import Location
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.contentstore.content import StaticContent
from xmodule.contentstore.django import _CONTENTSTORE

from xmodule.course_module import CourseDescriptor

from xmodule.exceptions import NotFoundError
from uuid import uuid4
from pymongo import MongoClient

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class ContentStoreImportTest(ModuleStoreTestCase):
    """
    Tests that rely on the toy and test_import_course courses.
    NOTE: refactor using CourseFactory so they do not.
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

    def tearDown(self):
        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'])
        _CONTENTSTORE.clear()

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
        _, content_store, course, course_location = self.load_test_import_course()

        # make sure we have ONE asset in our contentstore ("should_be_imported.html")
        all_assets, count = content_store.get_all_content_for_course(course_location)
        print "len(all_assets)=%d" % len(all_assets)
        self.assertEqual(len(all_assets), 1)
        self.assertEqual(count, 1)

        content = None
        try:
            location = StaticContent.get_location_from_path('/c4x/edX/test_import_course/asset/should_be_imported.html')
            content = content_store.find(location)
        except NotFoundError:
            pass

        self.assertIsNotNone(content)

        # make sure course.static_asset_path is correct
        print "static_asset_path = {0}".format(course.static_asset_path)
        self.assertEqual(course.static_asset_path, 'test_import_course')

    def test_asset_import_nostatic(self):
        '''
        This test validates that an image asset is NOT imported when do_import_static=False
        '''
        content_store = contentstore()

        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store, do_import_static=False, verbose=True)

        course_location = CourseDescriptor.id_to_location('edX/toy/2012_Fall')
        module_store.get_item(course_location)

        # make sure we have NO assets in our contentstore
        all_assets, count = content_store.get_all_content_for_course(course_location)
        self.assertEqual(len(all_assets), 0)
        self.assertEqual(count, 0)

    def test_no_static_link_rewrites_on_import(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], do_import_static=False, verbose=True)

        handouts = module_store.get_item(Location(['i4x', 'edX', 'toy', 'course_info', 'handouts', None]))
        self.assertIn('/static/', handouts.data)

        handouts = module_store.get_item(Location(['i4x', 'edX', 'toy', 'html', 'toyhtml', None]))
        self.assertIn('/static/', handouts.data)

    def test_tab_name_imports_correctly(self):
        _module_store, _content_store, course, _course_location = self.load_test_import_course()
        print "course tabs = {0}".format(course.tabs)
        self.assertEqual(course.tabs[2]['name'], 'Syllabus')

    def test_rewrite_reference_list(self):
        module_store = modulestore('direct')
        target_location = Location(['i4x', 'testX', 'conditional_copy', 'course', 'copy_run'])
        import_from_xml(
            module_store,
            'common/test/data/',
            ['conditional'],
            target_location_namespace=target_location
        )
        conditional_module = module_store.get_item(
            Location(['i4x', 'testX', 'conditional_copy', 'conditional', 'condone'])
        )
        self.assertIsNotNone(conditional_module)
        self.assertListEqual(
            [
                u'i4x://testX/conditional_copy/problem/choiceprob',
                u'i4x://edX/different_course/html/for_testing_import_rewrites'
            ],
            conditional_module.sources_list
        )
        self.assertListEqual(
            [
                u'i4x://testX/conditional_copy/html/congrats',
                u'i4x://testX/conditional_copy/html/secret_page'
            ],
            conditional_module.show_tag_list
        )

    def test_rewrite_reference(self):
        module_store = modulestore('direct')
        target_location = Location(['i4x', 'testX', 'peergrading_copy', 'course', 'copy_run'])
        import_from_xml(
            module_store,
            'common/test/data/',
            ['open_ended'],
            target_location_namespace=target_location
        )
        peergrading_module = module_store.get_item(
            Location(['i4x', 'testX', 'peergrading_copy', 'peergrading', 'PeerGradingLinked'])
        )
        self.assertIsNotNone(peergrading_module)
        self.assertEqual(
            u'i4x://testX/peergrading_copy/combinedopenended/SampleQuestion',
            peergrading_module.link_to_location
        )
