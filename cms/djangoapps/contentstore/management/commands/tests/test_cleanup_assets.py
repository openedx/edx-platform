"""
Test for assets cleanup of courses for Mac OS metadata files (with filename ".DS_Store"
or with filename which starts with "._")
"""
from django.core.management import call_command

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xmodule.contentstore.content import XASSET_LOCATION_TAG
from xmodule.contentstore.django import contentstore
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.mongo.base import location_to_query
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.xml_importer import import_from_xml
from django.conf import settings

TEST_DATA_DIR = settings.COMMON_TEST_DATA_ROOT


class ExportAllCourses(ModuleStoreTestCase):
    """
    Tests assets cleanup for all courses.
    """
    def setUp(self):
        """ Common setup. """
        self.content_store = contentstore()
        self.module_store = modulestore()

    def test_export_all_courses(self):
        """
        This test validates that redundant Mac metadata files ('._example.txt', '.DS_Store') are
        cleaned up on import
        """
        import_from_xml(
            self.module_store,
            '**replace_user**',
            TEST_DATA_DIR,
            ['dot-underscore'],
            static_content_store=self.content_store,
            do_import_static=True,
            verbose=True
        )

        course = self.module_store.get_course(SlashSeparatedCourseKey('edX', 'dot-underscore', '2014_Fall'))
        self.assertIsNotNone(course)

        # check that there are two assets ['example.txt', '.example.txt'] in contentstore for imported course
        all_assets, count = self.content_store.get_all_content_for_course(course.id)
        self.assertEqual(count, 2)
        self.assertEqual(set([asset['_id']['name'] for asset in all_assets]), set([u'.example.txt', u'example.txt']))

        # manually add redundant assets (file ".DS_Store" and filename starts with "._")
        course_filter = course.id.make_asset_key("asset", None)
        query = location_to_query(course_filter, wildcard=True, tag=XASSET_LOCATION_TAG)
        query['_id.name'] = all_assets[0]['_id']['name']
        asset_doc = self.content_store.fs_files.find_one(query)
        asset_doc['_id']['name'] = u'._example_test.txt'
        self.content_store.fs_files.insert(asset_doc)
        asset_doc['_id']['name'] = u'.DS_Store'
        self.content_store.fs_files.insert(asset_doc)

        # check that now course has four assets
        all_assets, count = self.content_store.get_all_content_for_course(course.id)
        self.assertEqual(count, 4)
        self.assertEqual(
            set([asset['_id']['name'] for asset in all_assets]),
            set([u'.example.txt', u'example.txt', u'._example_test.txt', u'.DS_Store'])
        )
        # now call asset_cleanup command and check that there is only two proper assets in contentstore for the course
        call_command('cleanup_assets')
        all_assets, count = self.content_store.get_all_content_for_course(course.id)
        self.assertEqual(count, 2)
        self.assertEqual(set([asset['_id']['name'] for asset in all_assets]), set([u'.example.txt', u'example.txt']))
