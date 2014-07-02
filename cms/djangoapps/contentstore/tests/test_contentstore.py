# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=W0212

import copy
import mock
import shutil

from datetime import timedelta
from fs.osfs import OSFS
from json import loads
from path import path
from tempdir import mkdtemp_clean
from textwrap import dedent
from uuid import uuid4

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.utils import override_settings

from contentstore.tests.utils import parse_json, AjaxEnabledTestClient, CourseTestCase
from contentstore.views.component import ADVANCED_COMPONENT_TYPES

from xmodule.contentstore.django import contentstore, _CONTENTSTORE
from xmodule.contentstore.utils import restore_asset_from_trashcan, empty_asset_trashcan
from xmodule.exceptions import NotFoundError, InvalidVersionError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.inheritance import own_metadata
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, AssetLocation
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.xml_importer import import_from_xml, perform_xlint

from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor
from xmodule.seq_module import SequenceDescriptor

from contentstore.utils import delete_course_and_groups, reverse_url, reverse_course_url
from django_comment_common.utils import are_permissions_roles_seeded

from student import auth
from student.models import CourseEnrollment
from student.roles import CourseCreatorRole, CourseInstructorRole
from opaque_keys import InvalidKeyError
from contentstore.tests.utils import get_url


TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


class MongoCollectionFindWrapper(object):
    def __init__(self, original):
        self.original = original
        self.counter = 0

    def find(self, query, *args, **kwargs):
        self.counter = self.counter + 1
        return self.original(query, *args, **kwargs)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ContentStoreTestCase(CourseTestCase):
    """
    Base class for Content Store Test Cases
    """
    pass

class ContentStoreToyCourseTest(ContentStoreTestCase):
    """
    Tests that rely on the toy courses.
    TODO: refactor using CourseFactory so they do not.
    """
    def tearDown(self):
        contentstore().drop_database()
        _CONTENTSTORE.clear()

    def check_components_on_page(self, component_types, expected_types):
        """
        Ensure that the right types end up on the page.

        component_types is the list of advanced components.

        expected_types is the list of elements that should appear on the page.

        expected_types and component_types should be similar, but not
        exactly the same -- for example, 'video' in
        component_types should cause 'Video' to be present.
        """
        store = self.store
        _, course_items = import_from_xml(store, self.user.id, 'common/test/data/', ['simple'])
        course = course_items[0]
        course.advanced_modules = component_types
        store.update_item(course, self.user.id)

        # just pick one vertical
        descriptor = store.get_items(course.id, category='vertical',)
        resp = self.client.get_html(get_url('unit_handler', descriptor[0].location))
        self.assertEqual(resp.status_code, 200)

        for expected in expected_types:
            self.assertIn(expected, resp.content)

    def test_advanced_components_in_edit_unit(self):
        # This could be made better, but for now let's just assert that we see the advanced modules mentioned in the page
        # response HTML
        self.check_components_on_page(
            ADVANCED_COMPONENT_TYPES,
            ['Word cloud', 'Annotation', 'Text Annotation', 'Video Annotation', 'Image Annotation',
             'Open Response Assessment', 'Peer Grading Interface', 'split_test'],
        )

    def test_advanced_components_require_two_clicks(self):
        self.check_components_on_page(['word_cloud'], ['Word cloud'])

    def test_malformed_edit_unit_request(self):
        store = self.store
        _, course_items = import_from_xml(store, self.user.id, 'common/test/data/', ['simple'])

        # just pick one vertical
        usage_key = course_items[0].id.make_usage_key('vertical', None)

        resp = self.client.get_html(get_url('unit_handler', usage_key))
        self.assertEqual(resp.status_code, 400)

    def check_edit_unit(self, test_course_name):
        """Verifies the editing HTML in all the verticals in the given test course"""
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', [test_course_name])

        items = self.store.get_items(course_items[0].id, category='vertical')
        self._check_verticals(items)

    def test_edit_unit_toy(self):
        self.check_edit_unit('toy')

    def _get_draft_counts(self, item):
        cnt = 1 if getattr(item, 'is_draft', False) else 0
        for child in item.get_children():
            cnt = cnt + self._get_draft_counts(child)

        return cnt

    def test_get_items(self):
        '''
        This verifies a bug we had where the None setting in get_items() meant 'wildcard'
        Unfortunately, None = published for the revision field, so get_items() would return
        both draft and non-draft copies.
        '''
        store = self.store
        _, course_items = import_from_xml(store, self.user.id, 'common/test/data/', ['simple'])
        course_key = course_items[0].id
        html_usage_key = course_key.make_usage_key('html', 'test_html')

        html_module_from_draft_store = store.get_item(html_usage_key)
        store.convert_to_draft(html_module_from_draft_store.location, self.user.id)

        # Query get_items() and find the html item. This should just return back a single item (not 2).
        direct_store_items = store.get_items(course_key, revision=ModuleStoreEnum.RevisionOption.published_only)
        html_items_from_direct_store = [item for item in direct_store_items if (item.location == html_usage_key)]
        self.assertEqual(len(html_items_from_direct_store), 1)
        self.assertFalse(getattr(html_items_from_direct_store[0], 'is_draft', False))

        # Fetch from the draft store.
        draft_store_items = store.get_items(course_key, revision=ModuleStoreEnum.RevisionOption.draft_only)
        html_items_from_draft_store = [item for item in draft_store_items if (item.location == html_usage_key)]
        self.assertEqual(len(html_items_from_draft_store), 1)
        self.assertTrue(getattr(html_items_from_draft_store[0], 'is_draft', False))


    def test_draft_metadata(self):
        '''
        This verifies a bug we had where inherited metadata was getting written to the
        module as 'own-metadata' when publishing. Also verifies the metadata inheritance is
        properly computed
        '''
        draft_store = self.store
        import_from_xml(draft_store, self.user.id, 'common/test/data/', ['simple'])

        course_key = SlashSeparatedCourseKey('edX', 'simple', '2012_Fall')
        html_usage_key = course_key.make_usage_key('html', 'test_html')
        course = draft_store.get_course(course_key)
        html_module = draft_store.get_item(html_usage_key)

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        draft_store.convert_to_draft(html_module.location, self.user.id)

        # refetch to check metadata
        html_module = draft_store.get_item(html_usage_key)

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        # publish module
        draft_store.publish(html_module.location, self.user.id)

        # refetch to check metadata
        html_module = draft_store.get_item(html_usage_key)

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        # put back in draft and change metadata and see if it's now marked as 'own_metadata'
        draft_store.convert_to_draft(html_module.location, self.user.id)
        html_module = draft_store.get_item(html_usage_key)

        new_graceperiod = timedelta(hours=1)

        self.assertNotIn('graceperiod', own_metadata(html_module))
        html_module.graceperiod = new_graceperiod
        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        html_module.save()
        self.assertIn('graceperiod', own_metadata(html_module))
        self.assertEqual(html_module.graceperiod, new_graceperiod)

        draft_store.update_item(html_module, self.user.id)

        # read back to make sure it reads as 'own-metadata'
        html_module = draft_store.get_item(html_usage_key)

        self.assertIn('graceperiod', own_metadata(html_module))
        self.assertEqual(html_module.graceperiod, new_graceperiod)

        # republish
        draft_store.publish(html_module.location, self.user.id)

        # and re-read and verify 'own-metadata'
        draft_store.convert_to_draft(html_module.location, self.user.id)
        html_module = draft_store.get_item(html_usage_key)

        self.assertIn('graceperiod', own_metadata(html_module))
        self.assertEqual(html_module.graceperiod, new_graceperiod)

    def test_get_depth_with_drafts(self):
        store = self.store
        import_from_xml(store, self.user.id, 'common/test/data/', ['simple'])

        course_key = SlashSeparatedCourseKey('edX', 'simple', '2012_Fall')
        course = store.get_course(course_key)

        # make sure no draft items have been returned
        num_drafts = self._get_draft_counts(course)
        self.assertEqual(num_drafts, 0)

        problem_usage_key = course_key.make_usage_key('problem', 'ps01-simple')
        problem = store.get_item(problem_usage_key)

        # put into draft
        store.convert_to_draft(problem.location, self.user.id)

        # make sure we can query that item and verify that it is a draft
        draft_problem = store.get_item(problem_usage_key)
        self.assertTrue(getattr(draft_problem, 'is_draft', False))

        # now requery with depth
        course = store.get_course(course_key)

        # make sure just one draft item have been returned
        num_drafts = self._get_draft_counts(course)
        self.assertEqual(num_drafts, 1)

    def test_no_static_link_rewrites_on_import(self):
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course = course_items[0]

        handouts_usage_key = course.id.make_usage_key('course_info', 'handouts')
        handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('/static/', handouts.data)

        handouts_usage_key = course.id.make_usage_key('html', 'toyhtml')
        handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('/static/', handouts.data)

    @mock.patch('xmodule.course_module.requests.get')
    def test_import_textbook_as_content_element(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course = self.store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))
        self.assertGreater(len(course.textbooks), 0)

    def test_import_polls(self):
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_key = course_items[0].id

        items = self.store.get_items(course_key, category='poll_question')
        found = len(items) > 0

        self.assertTrue(found)
        # check that there's actually content in the 'question' field
        self.assertGreater(len(items[0].question), 0)

    def test_xlint_fails(self):
        err_cnt = perform_xlint('common/test/data', ['toy'])
        self.assertGreater(err_cnt, 0)

    @override_settings(COURSES_WITH_UNSAFE_CODE=['edX/toy/.*'])
    def test_module_preview_in_whitelist(self):
        """
        Tests the ajax callback to render an XModule
        """
        direct_store = self.store
        _, course_items = import_from_xml(direct_store, self.user.id, 'common/test/data/', ['toy'])
        usage_key = course_items[0].id.make_usage_key('vertical', 'vertical_test')
        # also try a custom response which will trigger the 'is this course in whitelist' logic
        resp = self.client.get_json(
            get_url('xblock_view_handler', usage_key, kwargs={'view_name': 'container_preview'})
        )
        self.assertEqual(resp.status_code, 200)

        # These are the data-ids of the xblocks contained in the vertical.
        self.assertContains(resp, 'edX/toy/video/sample_video')
        self.assertContains(resp, 'edX/toy/video/separate_file_video')
        self.assertContains(resp, 'edX/toy/video/video_with_end_time')
        self.assertContains(resp, 'edX/toy/poll_question/T1_changemind_poll_foo_2')

    def test_delete(self):
        store = self.store
        course = CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')

        chapterloc = ItemFactory.create(parent_location=course.location, display_name="Chapter").location
        ItemFactory.create(parent_location=chapterloc, category='sequential', display_name="Sequential")

        sequential_key = course.id.make_usage_key('sequential', 'Sequential')
        sequential = store.get_item(sequential_key)
        chapter_key = course.id.make_usage_key('chapter', 'Chapter')
        chapter = store.get_item(chapter_key)

        # make sure the parent points to the child object which is to be deleted
        self.assertTrue(sequential.location in chapter.children)

        self.client.delete(get_url('xblock_handler', sequential_key))

        found = False
        try:
            store.get_item(sequential_key)
            found = True
        except ItemNotFoundError:
            pass

        self.assertFalse(found)

        chapter = store.get_item(chapter_key)

        # make sure the parent no longer points to the child object which was deleted
        self.assertFalse(sequential.location in chapter.children)

    def test_about_overrides(self):
        '''
        This test case verifies that a course can use specialized override for about data, e.g. /about/Fall_2012/effort.html
        while there is a base definition in /about/effort.html
        '''
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_key = course_items[0].id
        effort = self.store.get_item(course_key.make_usage_key('about', 'effort'))
        self.assertEqual(effort.data, '6 hours')

        # this one should be in a non-override folder
        effort = self.store.get_item(course_key.make_usage_key('about', 'end_date'))
        self.assertEqual(effort.data, 'TBD')

    def test_asset_import(self):
        '''
        This test validates that an image asset is imported and a thumbnail was generated for a .gif
        '''
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], static_content_store=content_store, verbose=True)

        course = self.store.get_course(SlashSeparatedCourseKey('edX', 'toy', '2012_Fall'))

        self.assertIsNotNone(course)

        # make sure we have some assets in our contentstore
        all_assets, __ = content_store.get_all_content_for_course(course.id)
        self.assertGreater(len(all_assets), 0)

        # make sure we have some thumbnails in our contentstore
        content_store.get_all_content_thumbnails_for_course(course.id)

        #
        # cdodge: temporarily comment out assertion on thumbnails because many environments
        # will not have the jpeg converter installed and this test will fail
        #
        #
        # self.assertGreater(len(all_thumbnails), 0)

        content = None
        try:
            location = AssetLocation.from_deprecated_string('/c4x/edX/toy/asset/sample_static.txt')
            content = content_store.find(location)
        except NotFoundError:
            pass

        self.assertIsNotNone(content)

        #
        # cdodge: temporarily comment out assertion on thumbnails because many environments
        # will not have the jpeg converter installed and this test will fail
        #
        # self.assertIsNotNone(content.thumbnail_location)
        #
        # thumbnail = None
        # try:
        #    thumbnail = content_store.find(content.thumbnail_location)
        # except:
        #    pass
        #
        # self.assertIsNotNone(thumbnail)

    def test_asset_delete_and_restore(self):
        '''
        This test will exercise the soft delete/restore functionality of the assets
        '''
        content_store, trash_store, thumbnail_location, _location = self._delete_asset_in_course()
        asset_location = AssetLocation.from_deprecated_string('/c4x/edX/toy/asset/sample_static.txt')

        # now try to find it in store, but they should not be there any longer
        content = content_store.find(asset_location, throw_on_not_found=False)
        self.assertIsNone(content)

        if thumbnail_location:
            thumbnail = content_store.find(thumbnail_location, throw_on_not_found=False)
            self.assertIsNone(thumbnail)

        # now try to find it and the thumbnail in trashcan - should be in there
        content = trash_store.find(asset_location, throw_on_not_found=False)
        self.assertIsNotNone(content)

        if thumbnail_location:
            thumbnail = trash_store.find(thumbnail_location, throw_on_not_found=False)
            self.assertIsNotNone(thumbnail)

        # let's restore the asset
        restore_asset_from_trashcan('/c4x/edX/toy/asset/sample_static.txt')

        # now try to find it in courseware store, and they should be back after restore
        content = content_store.find(asset_location, throw_on_not_found=False)
        self.assertIsNotNone(content)

        if thumbnail_location:
            thumbnail = content_store.find(thumbnail_location, throw_on_not_found=False)
            self.assertIsNotNone(thumbnail)

    def _delete_asset_in_course(self):
        """
        Helper method for:
          1) importing course from xml
          2) finding asset in course (verifying non-empty)
          3) computing thumbnail location of asset
          4) deleting the asset from the course
        """

        content_store = contentstore()
        trash_store = contentstore('trashcan')
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], static_content_store=content_store)

        # look up original (and thumbnail) in content store, should be there after import
        location = AssetLocation.from_deprecated_string('/c4x/edX/toy/asset/sample_static.txt')
        content = content_store.find(location, throw_on_not_found=False)
        thumbnail_location = content.thumbnail_location
        self.assertIsNotNone(content)

        #
        # cdodge: temporarily comment out assertion on thumbnails because many environments
        # will not have the jpeg converter installed and this test will fail
        #
        # self.assertIsNotNone(thumbnail_location)

        # go through the website to do the delete, since the soft-delete logic is in the view
        course = course_items[0]
        url = reverse_course_url(
            'assets_handler',
            course.id,
            kwargs={'asset_key_string': unicode(course.id.make_asset_key('asset', 'sample_static.txt'))}
        )
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        return content_store, trash_store, thumbnail_location, location

    def test_course_info_updates_import_export(self):
        """
        Test that course info updates are imported and exported with all content fields ('data', 'items')
        """
        content_store = contentstore()
        data_dir = "common/test/data/"
        import_from_xml(self.store, self.user.id, data_dir, ['course_info_updates'],
                        static_content_store=content_store, verbose=True)

        course_id = SlashSeparatedCourseKey('edX', 'course_info_updates', '2014_T1')
        course = self.store.get_course(course_id)

        self.assertIsNotNone(course)

        course_updates = self.store.get_item(course_id.make_usage_key('course_info', 'updates'))

        self.assertIsNotNone(course_updates)

        # check that course which is imported has files 'updates.html' and 'updates.items.json'
        filesystem = OSFS(data_dir + 'course_info_updates/info')
        self.assertTrue(filesystem.exists('updates.html'))
        self.assertTrue(filesystem.exists('updates.items.json'))

        # verify that course info update module has same data content as in data file from which it is imported
        # check 'data' field content
        with filesystem.open('updates.html', 'r') as course_policy:
            on_disk = course_policy.read()
            self.assertEqual(course_updates.data, on_disk)

        # check 'items' field content
        with filesystem.open('updates.items.json', 'r') as course_policy:
            on_disk = loads(course_policy.read())
            self.assertEqual(course_updates.items, on_disk)

        # now export the course to a tempdir and test that it contains files 'updates.html' and 'updates.items.json'
        # with same content as in course 'info' directory
        root_dir = path(mkdtemp_clean())
        print 'Exporting to tempdir = {0}'.format(root_dir)
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_export')

        # check that exported course has files 'updates.html' and 'updates.items.json'
        filesystem = OSFS(root_dir / 'test_export/info')
        self.assertTrue(filesystem.exists('updates.html'))
        self.assertTrue(filesystem.exists('updates.items.json'))

        # verify that exported course has same data content as in course_info_update module
        with filesystem.open('updates.html', 'r') as grading_policy:
            on_disk = grading_policy.read()
            self.assertEqual(on_disk, course_updates.data)

        with filesystem.open('updates.items.json', 'r') as grading_policy:
            on_disk = loads(grading_policy.read())
            self.assertEqual(on_disk, course_updates.items)

    def test_empty_trashcan(self):
        '''
        This test will exercise the emptying of the asset trashcan
        '''
        __, trash_store, __, _location = self._delete_asset_in_course()

        # make sure there's something in the trashcan
        course_id = SlashSeparatedCourseKey('edX', 'toy', '6.002_Spring_2012')
        all_assets, __ = trash_store.get_all_content_for_course(course_id)
        self.assertGreater(len(all_assets), 0)

        # make sure we have some thumbnails in our trashcan
        _all_thumbnails = trash_store.get_all_content_thumbnails_for_course(course_id)
        #
        # cdodge: temporarily comment out assertion on thumbnails because many environments
        # will not have the jpeg converter installed and this test will fail
        #
        # self.assertGreater(len(all_thumbnails), 0)

        # empty the trashcan
        empty_asset_trashcan([course_id])

        # make sure trashcan is empty
        all_assets, count = trash_store.get_all_content_for_course(course_id)
        self.assertEqual(len(all_assets), 0)
        self.assertEqual(count, 0)

        all_thumbnails = trash_store.get_all_content_thumbnails_for_course(course_id)
        self.assertEqual(len(all_thumbnails), 0)

    def test_illegal_draft_crud_ops(self):
        draft_store = self.store

        course = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        location = course.id.make_usage_key('chapter', 'neuvo')
        # Ensure draft mongo store does not create drafts for things that shouldn't be draft
        newobject = draft_store.create_and_save_xmodule(location, self.user.id)
        self.assertFalse(getattr(newobject, 'is_draft', False))
        with self.assertRaises(InvalidVersionError):
            draft_store.convert_to_draft(location, self.user.id)
        chapter = draft_store.get_item(location)
        chapter.data = 'chapter data'

        draft_store.update_item(chapter, self.user.id)
        newobject = draft_store.get_item(chapter.location)
        self.assertFalse(getattr(newobject, 'is_draft', False))

        with self.assertRaises(InvalidVersionError):
            draft_store.unpublish(location, self.user.id)

    def test_bad_contentstore_request(self):
        resp = self.client.get_html('http://localhost:8001/c4x/CDX/123123/asset/&images_circuits_Lab7Solution2.png')
        self.assertEqual(resp.status_code, 400)

    def test_rewrite_nonportable_links_on_import(self):
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], static_content_store=content_store)

        # first check a static asset link
        course_key = SlashSeparatedCourseKey('edX', 'toy', 'run')
        html_module_location = course_key.make_usage_key('html', 'nonportable')
        html_module = self.store.get_item(html_module_location)
        self.assertIn('/static/foo.jpg', html_module.data)

        # then check a intra courseware link
        html_module_location = course_key.make_usage_key('html', 'nonportable_link')
        html_module = self.store.get_item(html_module_location)
        self.assertIn('/jump_to_id/nonportable_link', html_module.data)

    def test_delete_course(self):
        """
        This test will import a course, make a draft item, and delete it. This will also assert that the
        draft content is also deleted
        """
        content_store = contentstore()

        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], static_content_store=content_store)

        course_id = course_items[0].id

        # get a vertical (and components in it) to put into DRAFT
        vertical = self.store.get_item(course_id.make_usage_key('vertical', 'vertical_test'), depth=1)

        self.store.convert_to_draft(vertical.location, self.user.id)

        # delete the course
        self.store.delete_course(course_id, self.user.id)

        # assert that there's absolutely no non-draft modules in the course
        # this should also include all draft items
        items = self.store.get_items(course_id)
        self.assertEqual(len(items), 0)

        # assert that all content in the asset library is also deleted
        assets, count = content_store.get_all_content_for_course(course_id)
        self.assertEqual(len(assets), 0)
        self.assertEqual(count, 0)

    def verify_content_existence(self, store, root_dir, course_id, dirname, category_name, filename_suffix=''):
        filesystem = OSFS(root_dir / 'test_export')
        self.assertTrue(filesystem.exists(dirname))

        items = store.get_items(course_id, category=category_name)

        for item in items:
            filesystem = OSFS(root_dir / ('test_export/' + dirname))
            self.assertTrue(filesystem.exists(item.location.name + filename_suffix))

    @mock.patch('xmodule.course_module.requests.get')
    def test_export_course_roundtrip(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        content_store = contentstore()
        course_id = self.import_and_populate_course()

        root_dir = path(mkdtemp_clean())
        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_export')

        # check for static tabs
        self.verify_content_existence(self.store, root_dir, course_id, 'tabs', 'static_tab', '.html')

        # check for about content
        self.verify_content_existence(self.store, root_dir, course_id, 'about', 'about', '.html')

        # check for grading_policy.json
        filesystem = OSFS(root_dir / 'test_export/policies/2012_Fall')
        self.assertTrue(filesystem.exists('grading_policy.json'))

        course = self.store.get_course(course_id)
        # compare what's on disk compared to what we have in our course
        with filesystem.open('grading_policy.json', 'r') as grading_policy:
            on_disk = loads(grading_policy.read())
            self.assertEqual(on_disk, course.grading_policy)

        # check for policy.json
        self.assertTrue(filesystem.exists('policy.json'))

        # compare what's on disk to what we have in the course module
        with filesystem.open('policy.json', 'r') as course_policy:
            on_disk = loads(course_policy.read())
            self.assertIn('course/2012_Fall', on_disk)
            self.assertEqual(on_disk['course/2012_Fall'], own_metadata(course))

        # remove old course
        self.store.delete_course(course_id, self.user.id)

        # reimport over old course
        self.check_import(root_dir, content_store, course_id)

        # import to different course id
        new_course_id = SlashSeparatedCourseKey('anotherX', 'anotherToy', 'Someday')
        self.check_import(root_dir, content_store, new_course_id)
        self.assertCoursesEqual(course_id, new_course_id)

        shutil.rmtree(root_dir)

    def check_import(self, root_dir, content_store, course_id):
        """Imports the course in root_dir into the given course_id and verifies its content"""
        # reimport
        import_from_xml(
            self.store,
            self.user.id,
            root_dir,
            ['test_export'],
            static_content_store=content_store,
            target_course_id=course_id,
        )

        # verify content of the course
        self.check_populated_course(course_id)

        # verify additional export attributes
        def verify_export_attrs_removed(attributes):
            """Verifies all temporary attributes added during export are removed"""
            self.assertNotIn('index_in_children_list', attributes)
            self.assertNotIn('parent_sequential_url', attributes)

        vertical = self.store.get_item(course_id.make_usage_key('vertical', self.TEST_VERTICAL))
        verify_export_attrs_removed(vertical.xml_attributes)

        for child in vertical.get_children():
            verify_export_attrs_removed(child.xml_attributes)
            if hasattr(child, 'data'):
                verify_export_attrs_removed(child.data)

    def test_export_course_with_metadata_only_video(self):
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        # create a new video module and add it as a child to a vertical
        # this re-creates a bug whereby since the video template doesn't have
        # anything in 'data' field, the export was blowing up
        verticals = self.store.get_items(course_id, category='vertical')

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        ItemFactory.create(parent_location=parent.location, category="video", display_name="untitled")

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_export')

        shutil.rmtree(root_dir)

    def test_export_course_with_metadata_only_word_cloud(self):
        """
        Similar to `test_export_course_with_metadata_only_video`.
        """
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['word_cloud'])
        course_id = SlashSeparatedCourseKey('HarvardX', 'ER22x', '2013_Spring')

        verticals = self.store.get_items(course_id, category='vertical')

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        ItemFactory.create(parent_location=parent.location, category="word_cloud", display_name="untitled")

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_export')

        shutil.rmtree(root_dir)

    def test_empty_data_roundtrip(self):
        """
        Test that an empty `data` field is preserved through
        export/import.
        """
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        verticals = self.store.get_items(course_id, category='vertical')

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        # Create a module, and ensure that its `data` field is empty
        word_cloud = ItemFactory.create(parent_location=parent.location, category="word_cloud", display_name="untitled")
        del word_cloud.data
        self.assertEquals(word_cloud.data, '')

        # Export the course
        root_dir = path(mkdtemp_clean())
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_roundtrip')

        # Reimport and get the video back
        import_from_xml(self.store, self.user.id, root_dir)
        imported_word_cloud = self.store.get_item(course_id.make_usage_key('word_cloud', 'untitled'))

        # It should now contain empty data
        self.assertEquals(imported_word_cloud.data, '')

    def test_html_export_roundtrip(self):
        """
        Test that a course which has HTML that has style formatting is preserved in export/import
        """
        content_store = contentstore()

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])

        course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        # Export the course
        root_dir = path(mkdtemp_clean())
        export_to_xml(self.store, content_store, course_id, root_dir, 'test_roundtrip')

        # Reimport and get the video back
        import_from_xml(self.store, self.user.id, root_dir)

        # get the sample HTML with styling information
        html_module = self.store.get_item(course_id.make_usage_key('html', 'with_styling'))
        self.assertIn('<p style="font:italic bold 72px/30px Georgia, serif; color: red; ">', html_module.data)

        # get the sample HTML with just a simple <img> tag information
        html_module = self.store.get_item(course_id.make_usage_key('html', 'just_img'))
        self.assertIn('<img src="/static/foo_bar.jpg" />', html_module.data)

    def test_course_handouts_rewrites(self):
        # import a test course
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_id = course_items[0].id

        handouts_location = course_id.make_usage_key('course_info', 'handouts')

        # get module info (json)
        resp = self.client.get(get_url('xblock_handler', handouts_location))

        # make sure we got a successful response
        self.assertEqual(resp.status_code, 200)
        # check that /static/ has been converted to the full path
        # note, we know the link it should be because that's what in the 'toy' course in the test data
        self.assertContains(resp, '/c4x/edX/toy/asset/handouts_sample_handout.txt')

    def test_prefetch_children(self):
        mongo_store = self.store._get_modulestore_by_type(ModuleStoreEnum.Type.mongo)
        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')

        wrapper = MongoCollectionFindWrapper(mongo_store.collection.find)
        mongo_store.collection.find = wrapper.find

        # set the branch to 'publish' in order to prevent extra lookups of draft versions
        with mongo_store.branch_setting(ModuleStoreEnum.Branch.published_only):
            course = mongo_store.get_course(course_id, depth=2)

            # make sure we haven't done too many round trips to DB
            # note we say 3 round trips here for 1) the course, and 2 & 3) for the chapters and sequentials
            # Because we're querying from the top of the tree, we cache information needed for inheritance,
            # so we don't need to make an extra query to compute it.
            self.assertEqual(wrapper.counter, 3)

            # make sure we pre-fetched a known sequential which should be at depth=2
            self.assertTrue(course_id.make_usage_key('sequential', 'vertical_sequential') in course.system.module_data)

            # make sure we don't have a specific vertical which should be at depth=3
            self.assertFalse(course_id.make_usage_key('vertical', 'vertical_test') in course.system.module_data)

        # Now, test with the branch set to draft.  We should have one extra round trip call to check for
        # the existence of the draft versions
        wrapper.counter = 0
        mongo_store.get_course(course_id, depth=2)
        self.assertEqual(wrapper.counter, 4)


    def test_export_course_without_content_store(self):
        content_store = contentstore()

        # Create toy course

        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course_id = course_items[0].id

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)
        export_to_xml(self.store, None, course_id, root_dir, 'test_export_no_content_store')

        # Delete the course from module store and reimport it

        self.store.delete_course(course_id, self.user.id)

        import_from_xml(
            self.store, self.user.id, root_dir, ['test_export_no_content_store'],
            static_content_store=None,
            target_course_id=course_id
        )

        # Verify reimported course

        items = self.store.get_items(
            course_id,
            category='sequential',
            name='vertical_sequential'
        )
        self.assertEqual(len(items), 1)

    def _check_verticals(self, items):
        """ Test getting the editing HTML for each vertical. """
        # Assert is here to make sure that the course being tested actually has verticals (units) to check.
        self.assertGreater(len(items), 0)
        for descriptor in items:
            resp = self.client.get_html(get_url('unit_handler', descriptor.location))
            self.assertEqual(resp.status_code, 200)


class ContentStoreTest(ContentStoreTestCase):
    """
    Tests for the CMS ContentStore application.
    """
    def setUp(self):
        super(ContentStoreTest, self).setUp()

        self.course_data = {
            'org': 'MITx',
            'number': '111',
            'display_name': 'Robot Super Course',
            'run': '2013_Spring'
        }

    def tearDown(self):
        contentstore().drop_database()
        _CONTENTSTORE.clear()

    def assert_created_course(self, number_suffix=None):
        """
        Checks that the course was created properly.
        """
        test_course_data = {}
        test_course_data.update(self.course_data)
        if number_suffix:
            test_course_data['number'] = '{0}_{1}'.format(test_course_data['number'], number_suffix)
        course_key = _get_course_id(test_course_data)
        _create_course(self, course_key, test_course_data)
        # Verify that the creator is now registered in the course.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_key))
        return test_course_data

    def assert_create_course_failed(self, error_message):
        """
        Checks that the course not created.
        """
        resp = self.client.ajax_post('/course/', self.course_data)
        self.assertEqual(resp.status_code, 400)
        data = parse_json(resp)
        self.assertEqual(data['error'], error_message)

    def test_create_course(self):
        """Test new course creation - happy path"""
        self.assert_created_course()

    def test_create_course_with_dots(self):
        """Test new course creation with dots in the name"""
        self.course_data['org'] = 'org.foo.bar'
        self.course_data['number'] = 'course.number'
        self.course_data['run'] = 'run.name'
        self.assert_created_course()

    def test_create_course_check_forum_seeding(self):
        """Test new course creation and verify forum seeding """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        self.assertTrue(are_permissions_roles_seeded(_get_course_id(test_course_data)))

    def test_forum_unseeding_on_delete(self):
        """Test new course creation and verify forum unseeding """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        course_id = _get_course_id(test_course_data)
        self.assertTrue(are_permissions_roles_seeded(course_id))
        delete_course_and_groups(course_id, self.user.id)
        # should raise an exception for checking permissions on deleted course
        with self.assertRaises(ItemNotFoundError):
            are_permissions_roles_seeded(course_id)

    def test_forum_unseeding_with_multiple_courses(self):
        """Test new course creation and verify forum unseeding when there are multiple courses"""
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        second_course_data = self.assert_created_course(number_suffix=uuid4().hex)

        # unseed the forums for the first course
        course_id = _get_course_id(test_course_data)
        delete_course_and_groups(course_id, self.user.id)
        # should raise an exception for checking permissions on deleted course
        with self.assertRaises(ItemNotFoundError):
            are_permissions_roles_seeded(course_id)

        second_course_id = _get_course_id(second_course_data)
        # permissions should still be there for the other course
        self.assertTrue(are_permissions_roles_seeded(second_course_id))

    def test_course_enrollments_and_roles_on_delete(self):
        """
        Test that course deletion doesn't remove course enrollments or user's roles
        """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        course_id = _get_course_id(test_course_data)

        # test that a user gets his enrollment and its 'student' role as default on creating a course
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        self.assertTrue(self.user.roles.filter(name="Student", course_id=course_id))  # pylint: disable=no-member

        delete_course_and_groups(course_id, self.user.id)
        # check that user's enrollment for this course is not deleted
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has form role "Student" for this course even after deleting it
        self.assertTrue(self.user.roles.filter(name="Student", course_id=course_id))  # pylint: disable=no-member

    def test_course_access_groups_on_delete(self):
        """
        Test that course deletion removes users from 'instructor' and 'staff' groups of this course
        of all format e.g, 'instructor_edX/Course/Run', 'instructor_edX.Course.Run', 'instructor_Course'
        """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        course_id = _get_course_id(test_course_data)

        # Add user in possible groups and check that user in instructor groups of this course
        instructor_role = CourseInstructorRole(course_id)

        auth.add_users(self.user, instructor_role, self.user)

        self.assertTrue(len(instructor_role.users_with_role()) > 0)

        # Now delete course and check that user not in instructor groups of this course
        delete_course_and_groups(course_id, self.user.id)

        # Update our cached user since its roles have changed
        self.user = User.objects.get_by_natural_key(self.user.natural_key()[0])

        self.assertFalse(instructor_role.has_user(self.user))
        self.assertEqual(len(instructor_role.users_with_role()), 0)

    def test_create_course_duplicate_course(self):
        """Test new course creation - error path"""
        self.client.ajax_post('/course/', self.course_data)
        self.assert_course_creation_failed('There is already a course defined with the same organization, course number, and course run. Please change either organization or course number to be unique.')

    def assert_course_creation_failed(self, error_message):
        """
        Checks that the course did not get created
        """
        test_enrollment = False
        try:
            course_id = _get_course_id(self.course_data)
            initially_enrolled = CourseEnrollment.is_enrolled(self.user, course_id)
            test_enrollment = True
        except InvalidKeyError:
            # b/c the intent of the test with bad chars isn't to test auth but to test the handler, ignore
            pass
        resp = self.client.ajax_post('/course/', self.course_data)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertRegexpMatches(data['ErrMsg'], error_message)
        if test_enrollment:
            # One test case involves trying to create the same course twice. Hence for that course,
            # the user will be enrolled. In the other cases, initially_enrolled will be False.
            self.assertEqual(initially_enrolled, CourseEnrollment.is_enrolled(self.user, course_id))

    def test_create_course_duplicate_number(self):
        """Test new course creation - error path"""
        self.client.ajax_post('/course/', self.course_data)
        self.course_data['display_name'] = 'Robot Super Course Two'
        self.course_data['run'] = '2013_Summer'

        self.assert_course_creation_failed('There is already a course defined with the same organization, course number, and course run. Please change either organization or course number to be unique.')

    def test_create_course_case_change(self):
        """Test new course creation - error path due to case insensitive name equality"""
        self.course_data['number'] = 'capital'
        self.client.ajax_post('/course/', self.course_data)
        cache_current = self.course_data['org']
        self.course_data['org'] = self.course_data['org'].lower()
        self.assert_course_creation_failed('There is already a course defined with the same organization, course number, and course run. Please change either organization or course number to be unique.')
        self.course_data['org'] = cache_current

        self.client.ajax_post('/course/', self.course_data)
        cache_current = self.course_data['number']
        self.course_data['number'] = self.course_data['number'].upper()
        self.assert_course_creation_failed('There is already a course defined with the same organization, course number, and course run. Please change either organization or course number to be unique.')

    def test_course_substring(self):
        """
        Test that a new course can be created whose name is a substring of an existing course
        """
        self.client.ajax_post('/course/', self.course_data)
        cache_current = self.course_data['number']
        self.course_data['number'] = '{}a'.format(self.course_data['number'])
        resp = self.client.ajax_post('/course/', self.course_data)
        self.assertEqual(resp.status_code, 200)
        self.course_data['number'] = cache_current
        self.course_data['org'] = 'a{}'.format(self.course_data['org'])
        resp = self.client.ajax_post('/course/', self.course_data)
        self.assertEqual(resp.status_code, 200)

    def test_create_course_with_bad_organization(self):
        """Test new course creation - error path for bad organization name"""
        self.course_data['org'] = 'University of California, Berkeley'
        self.assert_course_creation_failed(
            r"(?s)Unable to create course 'Robot Super Course'.*: Invalid characters in u'University of California, Berkeley'")

    def test_create_course_with_course_creation_disabled_staff(self):
        """Test new course creation -- course creation disabled, but staff access."""
        with mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_COURSE_CREATION': True}):
            self.assert_created_course()

    def test_create_course_with_course_creation_disabled_not_staff(self):
        """Test new course creation -- error path for course creation disabled, not staff access."""
        with mock.patch.dict('django.conf.settings.FEATURES', {'DISABLE_COURSE_CREATION': True}):
            self.user.is_staff = False
            self.user.save()
            self.assert_course_permission_denied()

    def test_create_course_no_course_creators_staff(self):
        """Test new course creation -- course creation group enabled, staff, group is empty."""
        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_CREATOR_GROUP': True}):
            self.assert_created_course()

    def test_create_course_no_course_creators_not_staff(self):
        """Test new course creation -- error path for course creator group enabled, not staff, group is empty."""
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            self.user.is_staff = False
            self.user.save()
            self.assert_course_permission_denied()

    def test_create_course_with_course_creator(self):
        """Test new course creation -- use course creator group"""
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            auth.add_users(self.user, CourseCreatorRole(), self.user)
            self.assert_created_course()

    def test_create_course_with_unicode_in_id_disabled(self):
        """
        Test new course creation with feature setting: ALLOW_UNICODE_COURSE_ID disabled.
        """
        with mock.patch.dict('django.conf.settings.FEATURES', {'ALLOW_UNICODE_COURSE_ID': False}):
            error_message = "Special characters not allowed in organization, course number, and course run."
            self.course_data['org'] = u'��������������'
            self.assert_create_course_failed(error_message)

            self.course_data['number'] = u'��chantillon'
            self.assert_create_course_failed(error_message)

            self.course_data['run'] = u'����������'
            self.assert_create_course_failed(error_message)

    def assert_course_permission_denied(self):
        """
        Checks that the course did not get created due to a PermissionError.
        """
        resp = self.client.ajax_post('/course/', self.course_data)
        self.assertEqual(resp.status_code, 403)

    def test_course_index_view_with_no_courses(self):
        """Test viewing the index page with no courses"""
        # Create a course so there is something to view
        resp = self.client.get_html('/course/')
        self.assertContains(
            resp,
            '<h1 class="page-header">My Courses</h1>',
            status_code=200,
            html=True
        )

    def test_course_factory(self):
        """Test that the course factory works correctly."""
        course = CourseFactory.create()
        self.assertIsInstance(course, CourseDescriptor)

    def test_item_factory(self):
        """Test that the item factory works correctly."""
        course = CourseFactory.create()
        item = ItemFactory.create(parent_location=course.location)
        self.assertIsInstance(item, SequenceDescriptor)

    def test_course_index_view_with_course(self):
        """Test viewing the index page with an existing course"""
        CourseFactory.create(display_name='Robot Super Educational Course')
        resp = self.client.get_html('/course/')
        self.assertContains(
            resp,
            '<h3 class="course-title">Robot Super Educational Course</h3>',
            status_code=200,
            html=True
        )

    def test_course_overview_view_with_course(self):
        """Test viewing the course overview page with an existing course"""
        course = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')
        resp = self._show_course_overview(course.id)
        self.assertContains(
            resp,
            '<article class="courseware-overview" data-locator="i4x://MITx/999/course/Robot_Super_Course" data-course-key="MITx/999/Robot_Super_Course">',
            status_code=200,
            html=True
        )

    def test_create_item(self):
        """Test creating a new xblock instance."""
        course = _course_factory_create_course()

        section_data = {
            'parent_locator': unicode(course.location),
            'category': 'chapter',
            'display_name': 'Section One',
        }

        resp = self.client.ajax_post(reverse_url('xblock_handler'), section_data)

        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertRegexpMatches(
            data['locator'],
            r"MITx/999/chapter/([0-9]|[a-f]){3,}$"
        )

    def test_capa_module(self):
        """Test that a problem treats markdown specially."""
        course = _course_factory_create_course()

        problem_data = {
            'parent_locator': unicode(course.location),
            'category': 'problem'
        }

        resp = self.client.ajax_post(reverse_url('xblock_handler'), problem_data)
        self.assertEqual(resp.status_code, 200)
        payload = parse_json(resp)
        problem_loc = UsageKey.from_string(payload['locator'])
        problem = self.store.get_item(problem_loc)
        # should be a CapaDescriptor
        self.assertIsInstance(problem, CapaDescriptor, "New problem is not a CapaDescriptor")
        context = problem.get_context()
        self.assertIn('markdown', context, "markdown is missing from context")
        self.assertNotIn('markdown', problem.editable_metadata_fields, "Markdown slipped into the editable metadata fields")

    def test_cms_imported_course_walkthrough(self):
        """
        Import and walk through some common URL endpoints. This just verifies non-500 and no other
        correct behavior, so it is not a deep test
        """
        def test_get_html(handler):
            # Helper function for getting HTML for a page in Studio and
            # checking that it does not error.
            resp = self.client.get_html(
                get_url(handler, course_key, 'course_key_string')
            )
            self.assertEqual(resp.status_code, 200)

        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['simple'])
        course_key = course_items[0].id

        resp = self._show_course_overview(course_key)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Chapter 2')

        # go to various pages
        test_get_html('import_handler')
        test_get_html('export_handler')
        test_get_html('course_team_handler')
        test_get_html('course_info_handler')
        test_get_html('checklists_handler')
        test_get_html('assets_handler')
        test_get_html('tabs_handler')
        test_get_html('settings_handler')
        test_get_html('grading_handler')
        test_get_html('advanced_settings_handler')
        test_get_html('textbooks_list_handler')

        # go look at a subsection page
        subsection_key = course_key.make_usage_key('sequential', 'test_sequence')
        resp = self.client.get_html(get_url('subsection_handler', subsection_key))
        self.assertEqual(resp.status_code, 200)

        # go look at the Edit page
        unit_key = course_key.make_usage_key('vertical', 'test_vertical')
        resp = self.client.get_html(get_url('unit_handler', unit_key))
        self.assertEqual(resp.status_code, 200)

        def delete_item(category, name):
            """ Helper method for testing the deletion of an xblock item. """
            item_key = course_key.make_usage_key(category, name)
            resp = self.client.delete(get_url('xblock_handler', item_key))
            self.assertEqual(resp.status_code, 204)

        # delete a component
        delete_item(category='html', name='test_html')

        # delete a unit
        delete_item(category='vertical', name='test_vertical')

        # delete a unit
        delete_item(category='sequential', name='test_sequence')

        # delete a chapter
        delete_item(category='chapter', name='chapter_2')

    def test_import_into_new_course_id(self):
        target_course_id = _get_course_id(self.course_data)
        _create_course(self, target_course_id, self.course_data)

        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], target_course_id=target_course_id)

        modules = self.store.get_items(target_course_id)

        # we should have a number of modules in there
        # we can't specify an exact number since it'll always be changing
        self.assertGreater(len(modules), 10)

        #
        # test various re-namespacing elements
        #

        # first check PDF textbooks, to make sure the url paths got updated
        course_module = self.store.get_course(target_course_id)

        self.assertEqual(len(course_module.pdf_textbooks), 1)
        self.assertEqual(len(course_module.pdf_textbooks[0]["chapters"]), 2)
        self.assertEqual(course_module.pdf_textbooks[0]["chapters"][0]["url"], '/static/Chapter1.pdf')
        self.assertEqual(course_module.pdf_textbooks[0]["chapters"][1]["url"], '/static/Chapter2.pdf')

    def test_import_into_new_course_id_wiki_slug_renamespacing(self):
        # If reimporting into the same course do not change the wiki_slug.
        target_course_id = SlashSeparatedCourseKey('edX', 'toy', '2012_Fall')
        course_data = {
            'org': target_course_id.org,
            'number': target_course_id.course,
            'display_name': 'Robot Super Course',
            'run': target_course_id.run
        }
        _create_course(self, target_course_id, course_data)
        course_module = self.store.get_course(target_course_id)
        course_module.wiki_slug = 'toy'
        course_module.save()

        # Import a course with wiki_slug == location.course
        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], target_course_id=target_course_id)
        course_module = self.store.get_course(target_course_id)
        self.assertEquals(course_module.wiki_slug, 'toy')

        # But change the wiki_slug if it is a different course.
        target_course_id = SlashSeparatedCourseKey('MITx', '111', '2013_Spring')
        course_data = {
            'org': target_course_id.org,
            'number': target_course_id.course,
            'display_name': 'Robot Super Course',
            'run': target_course_id.run
        }
        _create_course(self, target_course_id, course_data)

        # Import a course with wiki_slug == location.course
        import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'], target_course_id=target_course_id)
        course_module = self.store.get_course(target_course_id)
        self.assertEquals(course_module.wiki_slug, 'MITx.111.2013_Spring')

        # Now try importing a course with wiki_slug == '{0}.{1}.{2}'.format(location.org, location.course, location.run)
        import_from_xml(self.store, self.user.id, 'common/test/data/', ['two_toys'], target_course_id=target_course_id)
        course_module = self.store.get_course(target_course_id)
        self.assertEquals(course_module.wiki_slug, 'MITx.111.2013_Spring')

    def test_import_metadata_with_attempts_empty_string(self):
        import_from_xml(self.store, self.user.id, 'common/test/data/', ['simple'])
        did_load_item = False
        try:
            course_key = SlashSeparatedCourseKey('edX', 'simple', 'problem')
            usage_key = course_key.make_usage_key('problem', 'ps01-simple')
            self.store.get_item(usage_key)
            did_load_item = True
        except ItemNotFoundError:
            pass

        # make sure we found the item (e.g. it didn't error while loading)
        self.assertTrue(did_load_item)

    def test_forum_id_generation(self):
        course = CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')
        new_component_location = course.id.make_usage_key('discussion', 'new_component')

        # crate a new module and add it as a child to a vertical
        self.store.create_and_save_xmodule(new_component_location, self.user.id)

        new_discussion_item = self.store.get_item(new_component_location)

        self.assertNotEquals(new_discussion_item.discussion_id, '$$GUID$$')

    def test_metadata_inheritance(self):
        _, course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])

        course = course_items[0]
        verticals = self.store.get_items(course.id, category='vertical')

        # let's assert on the metadata_inheritance on an existing vertical
        for vertical in verticals:
            self.assertEqual(course.xqa_key, vertical.xqa_key)
            self.assertEqual(course.start, vertical.start)

        self.assertGreater(len(verticals), 0)

        new_component_location = course.id.make_usage_key('html', 'new_component')

        # crate a new module and add it as a child to a vertical
        new_object = self.store.create_xmodule(new_component_location)
        self.store.update_item(new_object, self.user.id, allow_not_found=True)
        parent = verticals[0]
        parent.children.append(new_component_location)
        self.store.update_item(parent, self.user.id)

        # flush the cache
        new_module = self.store.get_item(new_component_location)

        # check for grace period definition which should be defined at the course level
        self.assertEqual(parent.graceperiod, new_module.graceperiod)
        self.assertEqual(parent.start, new_module.start)
        self.assertEqual(course.start, new_module.start)

        self.assertEqual(course.xqa_key, new_module.xqa_key)

        #
        # now let's define an override at the leaf node level
        #
        new_module.graceperiod = timedelta(1)
        self.store.update_item(new_module, self.user.id)

        # flush the cache and refetch
        new_module = self.store.get_item(new_component_location)

        self.assertEqual(timedelta(1), new_module.graceperiod)

    def test_default_metadata_inheritance(self):
        course = CourseFactory.create()
        vertical = ItemFactory.create(parent_location=course.location)
        course.children.append(vertical)
        # in memory
        self.assertIsNotNone(course.start)
        self.assertEqual(course.start, vertical.start)
        self.assertEqual(course.textbooks, [])
        self.assertIn('GRADER', course.grading_policy)
        self.assertIn('GRADE_CUTOFFS', course.grading_policy)
        self.assertGreaterEqual(len(course.checklists), 4)

        # by fetching
        fetched_course = self.store.get_item(course.location)
        fetched_item = self.store.get_item(vertical.location)
        self.assertIsNotNone(fetched_course.start)
        self.assertEqual(course.start, fetched_course.start)
        self.assertEqual(fetched_course.start, fetched_item.start)
        self.assertEqual(course.textbooks, fetched_course.textbooks)
        # is this test too strict? i.e., it requires the dicts to be ==
        self.assertEqual(course.checklists, fetched_course.checklists)

    def test_image_import(self):
        """Test backwards compatibilty of course image."""
        content_store = contentstore()

        # Use conditional_and_poll, as it's got an image already
        import_from_xml(
            self.store,
            self.user.id,
            'common/test/data/',
            ['conditional_and_poll'],
            static_content_store=content_store
        )

        course = self.store.get_courses()[0]

        # Make sure the course image is set to the right place
        self.assertEqual(course.course_image, 'images_course_image.jpg')

        # Ensure that the imported course image is present -- this shouldn't raise an exception
        asset_key = course.id.make_asset_key('asset', course.course_image)
        content_store.find(asset_key)

    def _show_course_overview(self, course_key):
        """
        Show the course overview page.
        """
        resp = self.client.get_html(get_url('course_handler', course_key, 'course_key_string'))
        return resp

    def test_wiki_slug(self):
        """When creating a course a unique wiki_slug should be set."""

        course_key = _get_course_id(self.course_data)
        _create_course(self, course_key, self.course_data)
        course_module = self.store.get_course(course_key)
        self.assertEquals(course_module.wiki_slug, 'MITx.111.2013_Spring')


class MetadataSaveTestCase(ContentStoreTestCase):
    """Test that metadata is correctly cached and decached."""

    def setUp(self):
        super(MetadataSaveTestCase, self).setUp()

        course = CourseFactory.create(
            org='edX', course='999', display_name='Robot Super Course')

        video_sample_xml = '''
        <video display_name="Test Video"
                youtube="1.0:p2Q6BrNhdh8,0.75:izygArpw-Qo,1.25:1EeWXzPdhSA,1.5:rABDYkeK0x8"
                show_captions="false"
                from="00:00:01"
                to="00:01:00">
            <source src="http://www.example.com/file.mp4"/>
            <track src="http://www.example.com/track"/>
        </video>
        '''
        self.video_descriptor = ItemFactory.create(
            parent_location=course.location, category='video',
            data={'data': video_sample_xml}
        )

    def test_metadata_not_persistence(self):
        """
        Test that descriptors which set metadata fields in their
        constructor are correctly deleted.
        """
        self.assertIn('html5_sources', own_metadata(self.video_descriptor))
        attrs_to_strip = {
            'show_captions',
            'youtube_id_1_0',
            'youtube_id_0_75',
            'youtube_id_1_25',
            'youtube_id_1_5',
            'start_time',
            'end_time',
            'source',
            'html5_sources',
            'track'
        }

        location = self.video_descriptor.location

        for field_name in attrs_to_strip:
            delattr(self.video_descriptor, field_name)

        self.assertNotIn('html5_sources', own_metadata(self.video_descriptor))
        self.store.update_item(self.video_descriptor, self.user.id)
        module = self.store.get_item(location)

        self.assertNotIn('html5_sources', own_metadata(module))

    def test_metadata_persistence(self):
        # TODO: create the same test as `test_metadata_not_persistence`,
        # but check persistence for some other module.
        pass


class EntryPageTestCase(TestCase):
    """
    Tests entry pages that aren't specific to a course.
    """
    def setUp(self):
        self.client = AjaxEnabledTestClient()

    def _test_page(self, page, status_code=200):
        resp = self.client.get_html(page)
        self.assertEqual(resp.status_code, status_code)

    def test_how_it_works(self):
        self._test_page("/howitworks")

    def test_signup(self):
        self._test_page("/signup")

    def test_login(self):
        self._test_page("/signin")

    def test_logout(self):
        # Logout redirects.
        self._test_page("/logout", 302)


def _create_course(test, course_key, course_data):
    """
    Creates a course via an AJAX request and verifies the URL returned in the response.
    """
    course_url = get_url('course_handler', course_key, 'course_key_string')
    response = test.client.ajax_post(course_url, course_data)
    test.assertEqual(response.status_code, 200)
    data = parse_json(response)
    test.assertNotIn('ErrMsg', data)
    test.assertEqual(data['url'], course_url)


def _course_factory_create_course():
    """
    Creates a course via the CourseFactory and returns the locator for it.
    """
    return CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')


def _get_course_id(course_data):
    """Returns the course ID (org/number/run)."""
    return SlashSeparatedCourseKey(course_data['org'], course_data['number'], course_data['run'])
