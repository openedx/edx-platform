# -*- coding: utf-8 -*-
# pylint: disable=E1101
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

from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from opaque_keys.edx.locations import SlashSeparatedCourseKey, AssetLocation
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.contentstore.django import _CONTENTSTORE

from xmodule.exceptions import NotFoundError
from uuid import uuid4
from pymongo import MongoClient

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ContentStoreImportTest(ModuleStoreTestCase):
    """
    Tests that rely on the toy and test_import_course courses.
    NOTE: refactor using CourseFactory so they do not.
    """
    def setUp(self):

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
        Load the standard course used to test imports
        (for do_import_static=False behavior).
        '''
        content_store = contentstore()
        module_store = modulestore()
        import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data/',
            ['test_import_course'],
            static_content_store=content_store,
            do_import_static=False,
            verbose=True,
        )
        course_id = SlashSeparatedCourseKey('edX', 'test_import_course', '2012_Fall')
        course = module_store.get_course(course_id)
        self.assertIsNotNone(course)

        return module_store, content_store, course

    def test_import_course_into_similar_namespace(self):
        # Checks to make sure that a course with an org/course like
        # edx/course can be imported into a namespace with an org/course
        # like edx/course_name
        module_store, __, course = self.load_test_import_course()
        __, course_items = import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data',
            ['test_import_course_2'],
            target_course_id=course.id,
            verbose=True,
        )
        self.assertEqual(len(course_items), 1)

    def test_unicode_chars_in_course_name_import(self):
        """
        # Test that importing course with unicode 'id' and 'display name' doesn't give UnicodeEncodeError
        """
        module_store = modulestore()
        course_id = SlashSeparatedCourseKey(u'Юникода', u'unicode_course', u'échantillon')
        import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data/',
            ['2014_Uni'],
            target_course_id=course_id
        )

        course = module_store.get_course(course_id)
        self.assertIsNotNone(course)

        # test that course 'display_name' same as imported course 'display_name'
        self.assertEqual(course.display_name, u"Φυσικά το όνομα Unicode")

    def test_static_import(self):
        '''
        Stuff in static_import should always be imported into contentstore
        '''
        _, content_store, course = self.load_test_import_course()

        # make sure we have ONE asset in our contentstore ("should_be_imported.html")
        all_assets, count = content_store.get_all_content_for_course(course.id)
        print "len(all_assets)=%d" % len(all_assets)
        self.assertEqual(len(all_assets), 1)
        self.assertEqual(count, 1)

        content = None
        try:
            location = AssetLocation.from_deprecated_string(
                '/c4x/edX/test_import_course/asset/should_be_imported.html'
            )
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

        module_store = modulestore()
        import_from_xml(module_store, '**replace_user**', 'common/test/data/', ['toy'], static_content_store=content_store, do_import_static=False, verbose=True)

        course = module_store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))

        # make sure we have NO assets in our contentstore
        all_assets, count = content_store.get_all_content_for_course(course.id)
        self.assertEqual(len(all_assets), 0)
        self.assertEqual(count, 0)

    def test_no_static_link_rewrites_on_import(self):
        module_store = modulestore()
        _, courses = import_from_xml(module_store, '**replace_user**', 'common/test/data/', ['toy'], do_import_static=False, verbose=True)
        course_key = courses[0].id

        handouts = module_store.get_item(course_key.make_usage_key('course_info', 'handouts'))
        self.assertIn('/static/', handouts.data)

        handouts = module_store.get_item(course_key.make_usage_key('html', 'toyhtml'))
        self.assertIn('/static/', handouts.data)

    def test_tab_name_imports_correctly(self):
        _module_store, _content_store, course = self.load_test_import_course()
        print "course tabs = {0}".format(course.tabs)
        self.assertEqual(course.tabs[2]['name'], 'Syllabus')

    def test_rewrite_reference_list(self):
        module_store = modulestore()
        target_course_id = SlashSeparatedCourseKey('testX', 'conditional_copy', 'copy_run')
        import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data/',
            ['conditional'],
            target_course_id=target_course_id
        )
        conditional_module = module_store.get_item(
            target_course_id.make_usage_key('conditional', 'condone')
        )
        self.assertIsNotNone(conditional_module)
        different_course_id = SlashSeparatedCourseKey('edX', 'different_course', None)
        self.assertListEqual(
            [
                target_course_id.make_usage_key('problem', 'choiceprob'),
                different_course_id.make_usage_key('html', 'for_testing_import_rewrites')
            ],
            conditional_module.sources_list
        )
        self.assertListEqual(
            [
                target_course_id.make_usage_key('html', 'congrats'),
                target_course_id.make_usage_key('html', 'secret_page')
            ],
            conditional_module.show_tag_list
        )

    def test_rewrite_reference(self):
        module_store = modulestore()
        target_course_id = SlashSeparatedCourseKey('testX', 'peergrading_copy', 'copy_run')
        import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data/',
            ['open_ended'],
            target_course_id=target_course_id
        )
        peergrading_module = module_store.get_item(
            target_course_id.make_usage_key('peergrading', 'PeerGradingLinked')
        )
        self.assertIsNotNone(peergrading_module)
        self.assertEqual(
            target_course_id.make_usage_key('combinedopenended', 'SampleQuestion'),
            peergrading_module.link_to_location
        )

    def test_rewrite_reference_value_dict(self):
        module_store = modulestore()
        target_course_id = SlashSeparatedCourseKey('testX', 'split_test_copy', 'copy_run')
        import_from_xml(
            module_store,
            '**replace_user**',
            'common/test/data/',
            ['split_test_module'],
            target_course_id=target_course_id
        )
        split_test_module = module_store.get_item(
            target_course_id.make_usage_key('split_test', 'split1')
        )
        self.assertIsNotNone(split_test_module)
        self.assertEqual(
            {
                "0": target_course_id.make_usage_key('vertical', 'sample_0'),
                "2": target_course_id.make_usage_key('vertical', 'sample_2'),
            },
            split_test_module.group_id_to_child,
        )
