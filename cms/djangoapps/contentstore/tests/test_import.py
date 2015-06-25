# -*- coding: utf-8 -*-
# pylint: disable=no-member
# pylint: disable=protected-access
"""
Tests for import_course_from_xml using the mongo modulestore.
"""

from django.test.client import Client
from django.test.utils import override_settings
from django.conf import settings
import ddt
import copy

from openedx.core.djangoapps.content.course_structures.tests import SignalDisconnectTestMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.tests.factories import check_exact_number_of_calls, check_number_of_calls
from xmodule.modulestore.xml_importer import import_course_from_xml
from xmodule.exceptions import NotFoundError
from uuid import uuid4

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


@ddt.ddt
@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, SEARCH_ENGINE=None)
class ContentStoreImportTest(SignalDisconnectTestMixin, ModuleStoreTestCase):
    """
    Tests that rely on the toy and test_import_course courses.
    NOTE: refactor using CourseFactory so they do not.
    """
    def setUp(self):
        password = super(ContentStoreImportTest, self).setUp()

        self.client = Client()
        self.client.login(username=self.user.username, password=password)

    def load_test_import_course(self, target_id=None, create_if_not_present=True, module_store=None):
        '''
        Load the standard course used to test imports
        (for do_import_static=False behavior).
        '''
        content_store = contentstore()
        if module_store is None:
            module_store = modulestore()
        import_course_from_xml(
            module_store,
            self.user.id,
            TEST_DATA_DIR,
            ['test_import_course'],
            static_content_store=content_store,
            do_import_static=False,
            verbose=True,
            target_id=target_id,
            create_if_not_present=create_if_not_present,
        )
        course_id = module_store.make_course_key('edX', 'test_import_course', '2012_Fall')
        course = module_store.get_course(course_id)
        self.assertIsNotNone(course)

        return module_store, content_store, course

    def test_import_course_into_similar_namespace(self):
        # Checks to make sure that a course with an org/course like
        # edx/course can be imported into a namespace with an org/course
        # like edx/course_name
        module_store, __, course = self.load_test_import_course()
        course_items = import_course_from_xml(
            module_store,
            self.user.id,
            TEST_DATA_DIR,
            ['test_import_course_2'],
            target_id=course.id,
            verbose=True,
        )
        self.assertEqual(len(course_items), 1)

    def test_unicode_chars_in_course_name_import(self):
        """
        # Test that importing course with unicode 'id' and 'display name' doesn't give UnicodeEncodeError
        """
        # Test with the split modulestore because store.has_course fails in old mongo with unicode characters.
        with modulestore().default_store(ModuleStoreEnum.Type.split):
            module_store = modulestore()
            course_id = module_store.make_course_key(u'Юникода', u'unicode_course', u'échantillon')
            import_course_from_xml(
                module_store,
                self.user.id,
                TEST_DATA_DIR,
                ['2014_Uni'],
                target_id=course_id,
                create_if_not_present=True
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
            location = course.id.make_asset_key('asset', 'should_be_imported.html')
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
        import_course_from_xml(
            module_store, self.user.id, TEST_DATA_DIR, ['toy'],
            static_content_store=content_store, do_import_static=False,
            create_if_not_present=True, verbose=True
        )

        course = module_store.get_course(module_store.make_course_key('edX', 'toy', '2012_Fall'))

        # make sure we have NO assets in our contentstore
        all_assets, count = content_store.get_all_content_for_course(course.id)
        self.assertEqual(len(all_assets), 0)
        self.assertEqual(count, 0)

    def test_no_static_link_rewrites_on_import(self):
        module_store = modulestore()
        courses = import_course_from_xml(
            module_store, self.user.id, TEST_DATA_DIR, ['toy'], do_import_static=False, verbose=True,
            create_if_not_present=True
        )
        course_key = courses[0].id

        handouts = module_store.get_item(course_key.make_usage_key('course_info', 'handouts'))
        self.assertIn('/static/', handouts.data)

        handouts = module_store.get_item(course_key.make_usage_key('html', 'toyhtml'))
        self.assertIn('/static/', handouts.data)

    def test_tab_name_imports_correctly(self):
        _module_store, _content_store, course = self.load_test_import_course()
        print "course tabs = {0}".format(course.tabs)
        self.assertEqual(course.tabs[2]['name'], 'Syllabus')

    def test_import_performance_mongo(self):
        store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)

        # we try to refresh the inheritance tree for each update_item in the import
        with check_exact_number_of_calls(store, 'refresh_cached_metadata_inheritance_tree', 28):

            # _get_cached_metadata_inheritance_tree should be called only once
            with check_exact_number_of_calls(store, '_get_cached_metadata_inheritance_tree', 1):

                # with bulk-edit in progress, the inheritance tree should be recomputed only at the end of the import
                # NOTE: On Jenkins, with memcache enabled, the number of calls here is only 1.
                #       Locally, without memcache, the number of calls is actually 2 (once more during the publish step)
                with check_number_of_calls(store, '_compute_metadata_inheritance_tree', 2):
                    self.load_test_import_course(create_if_not_present=False, module_store=store)

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_reimport(self, default_ms_type):
        with modulestore().default_store(default_ms_type):
            __, __, course = self.load_test_import_course(create_if_not_present=True)
            self.load_test_import_course(target_id=course.id)

    def test_rewrite_reference_list(self):
        # This test fails with split modulestore (the HTML component is not in "different_course_id" namespace).
        # More investigation needs to be done.
        module_store = modulestore()._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)
        target_id = module_store.make_course_key('testX', 'conditional_copy', 'copy_run')
        import_course_from_xml(
            module_store,
            self.user.id,
            TEST_DATA_DIR,
            ['conditional'],
            target_id=target_id
        )
        conditional_module = module_store.get_item(
            target_id.make_usage_key('conditional', 'condone')
        )
        self.assertIsNotNone(conditional_module)
        different_course_id = module_store.make_course_key('edX', 'different_course', None)
        self.assertListEqual(
            [
                target_id.make_usage_key('problem', 'choiceprob'),
                different_course_id.make_usage_key('html', 'for_testing_import_rewrites')
            ],
            conditional_module.sources_list
        )
        self.assertListEqual(
            [
                target_id.make_usage_key('html', 'congrats'),
                target_id.make_usage_key('html', 'secret_page')
            ],
            conditional_module.show_tag_list
        )

    def test_rewrite_reference(self):
        module_store = modulestore()
        target_id = module_store.make_course_key('testX', 'peergrading_copy', 'copy_run')
        import_course_from_xml(
            module_store,
            self.user.id,
            TEST_DATA_DIR,
            ['open_ended'],
            target_id=target_id,
            create_if_not_present=True
        )
        peergrading_module = module_store.get_item(
            target_id.make_usage_key('peergrading', 'PeerGradingLinked')
        )
        self.assertIsNotNone(peergrading_module)
        self.assertEqual(
            target_id.make_usage_key('combinedopenended', 'SampleQuestion'),
            peergrading_module.link_to_location
        )

    def test_rewrite_reference_value_dict_published(self):
        """
        Test rewriting references in ReferenceValueDict, specifically with published content.
        """
        self._verify_split_test_import(
            'split_test_copy',
            'split_test_module',
            'split1',
            {"0": 'sample_0', "2": 'sample_2'},
        )

    def test_rewrite_reference_value_dict_draft(self):
        """
        Test rewriting references in ReferenceValueDict, specifically with draft content.
        """
        self._verify_split_test_import(
            'split_test_copy_with_draft',
            'split_test_module_draft',
            'fb34c21fe64941999eaead421a8711b8',
            {"0": '9f0941d021414798836ef140fb5f6841', "1": '0faf29473cf1497baa33fcc828b179cd'},
        )

    def _verify_split_test_import(self, target_course_name, source_course_name, split_test_name, groups_to_verticals):
        module_store = modulestore()
        target_id = module_store.make_course_key('testX', target_course_name, 'copy_run')
        import_course_from_xml(
            module_store,
            self.user.id,
            TEST_DATA_DIR,
            [source_course_name],
            target_id=target_id,
            create_if_not_present=True
        )
        split_test_module = module_store.get_item(
            target_id.make_usage_key('split_test', split_test_name)
        )
        self.assertIsNotNone(split_test_module)

        remapped_verticals = {
            key: target_id.make_usage_key('vertical', value) for key, value in groups_to_verticals.iteritems()
        }

        self.assertEqual(remapped_verticals, split_test_module.group_id_to_child)
