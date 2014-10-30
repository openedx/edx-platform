# -*- coding: utf-8 -*-
# pylint: disable=E1101
# pylint: disable=W0212

import copy
import mock
import shutil
import lxml

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

from xmodule.contentstore.django import contentstore
from xmodule.contentstore.utils import restore_asset_from_trashcan, empty_asset_trashcan
from xmodule.exceptions import NotFoundError, InvalidVersionError
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.inheritance import own_metadata
from opaque_keys.edx.keys import UsageKey, CourseKey
from opaque_keys.edx.locations import SlashSeparatedCourseKey, AssetLocation, CourseLocator
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, check_mongo_calls
from xmodule.modulestore.xml_exporter import export_to_xml
from xmodule.modulestore.xml_importer import import_from_xml, perform_xlint

from xmodule.capa_module import CapaDescriptor
from xmodule.course_module import CourseDescriptor, Textbook
from xmodule.seq_module import SequenceDescriptor

from contentstore.utils import delete_course_and_groups, reverse_url, reverse_course_url
from django_comment_common.utils import are_permissions_roles_seeded

from student import auth
from student.models import CourseEnrollment
from student.roles import CourseCreatorRole, CourseInstructorRole
from opaque_keys import InvalidKeyError
from contentstore.tests.utils import get_url
from course_action_state.models import CourseRerunState, CourseRerunUIStateManager

from course_action_state.managers import CourseActionStateItemNotFoundError
from xmodule.contentstore.content import StaticContent


TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE)
class ContentStoreTestCase(CourseTestCase):
    """
    Base class for Content Store Test Cases
    """


class ImportRequiredTestCases(ContentStoreTestCase):
    """
    Tests which legitimately need to import a course
    """
    def test_no_static_link_rewrites_on_import(self):
        course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
        course = course_items[0]

        handouts_usage_key = course.id.make_usage_key('course_info', 'handouts')
        handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('/static/', handouts.data)

        handouts_usage_key = course.id.make_usage_key('html', 'toyhtml')
        handouts = self.store.get_item(handouts_usage_key)
        self.assertIn('/static/', handouts.data)

    def test_xlint_fails(self):
        err_cnt = perform_xlint('common/test/data', ['toy'])
        self.assertGreater(err_cnt, 0)

    def test_about_overrides(self):
        '''
        This test case verifies that a course can use specialized override for about data,
        e.g. /about/Fall_2012/effort.html
        while there is a base definition in /about/effort.html
        '''
        course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
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

    def test_course_info_updates_import_export(self):
        """
        Test that course info updates are imported and exported with all content fields ('data', 'items')
        """
        content_store = contentstore()
        data_dir = "common/test/data/"
        courses = import_from_xml(
            self.store, self.user.id, data_dir, ['course_info_updates'],
            static_content_store=content_store, verbose=True,
        )

        course = courses[0]
        self.assertIsNotNone(course)

        course_updates = self.store.get_item(course.id.make_usage_key('course_info', 'updates'))
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
        export_to_xml(self.store, content_store, course.id, root_dir, 'test_export')

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

    def verify_content_existence(self, store, root_dir, course_id, dirname, category_name, filename_suffix=''):
        filesystem = OSFS(root_dir / 'test_export')
        self.assertTrue(filesystem.exists(dirname))

        items = store.get_items(course_id, qualifiers={'category': category_name})

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

        # assert that there is an html and video directory in drafts:
        draft_dir = OSFS(root_dir / 'test_export/drafts')
        self.assertTrue(draft_dir.exists('html'))
        self.assertTrue(draft_dir.exists('video'))
        # and assert that they contain the created modules
        self.assertIn(self.DRAFT_HTML + ".xml", draft_dir.listdir('html'))
        self.assertIn(self.DRAFT_VIDEO + ".xml", draft_dir.listdir('video'))

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
            self.assertNotIn('parent_url', attributes)

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
        verticals = self.store.get_items(course_id, qualifiers={'category': 'vertical'})

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

        verticals = self.store.get_items(course_id, qualifiers={'category': 'vertical'})

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

        verticals = self.store.get_items(course_id, qualifiers={'category': 'vertical'})

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

    def test_export_course_without_content_store(self):
        # Create toy course

        course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])
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
            qualifiers={
                'category': 'sequential',
                'name': 'vertical_sequential',
            }
        )
        self.assertEqual(len(items), 1)


class MiscCourseTests(ContentStoreTestCase):
    """
    Tests that rely on the toy courses.
    """
    def setUp(self):
        super(MiscCourseTests, self).setUp()
        # save locs not items b/c the items won't have the subsequently created children in them until refetched
        self.chapter_loc = self.store.create_child(
            self.user.id, self.course.location, 'chapter', 'test_chapter'
        ).location
        self.seq_loc = self.store.create_child(
            self.user.id, self.chapter_loc, 'sequential', 'test_seq'
        ).location
        self.vert_loc = self.store.create_child(self.user.id, self.seq_loc, 'vertical', 'test_vert').location
        # now create some things quasi like the toy course had
        self.problem = self.store.create_child(
            self.user.id, self.vert_loc, 'problem', 'test_problem', fields={
                "data": "<problem>Test</problem>"
            }
        )
        self.store.create_child(
            self.user.id, self.vert_loc, 'video', fields={
                "youtube_id_0_75": "JMD_ifUUfsU",
                "youtube_id_1_0": "OEoXaMPEzfM",
                "youtube_id_1_25": "AKqURZnYqpk",
                "youtube_id_1_5": "DYpADpL7jAY",
                "name": "sample_video",
            }
        )
        self.store.create_child(
            self.user.id, self.vert_loc, 'video', fields={
                "youtube_id_0_75": "JMD_ifUUfsU",
                "youtube_id_1_0": "OEoXaMPEzfM",
                "youtube_id_1_25": "AKqURZnYqpk",
                "youtube_id_1_5": "DYpADpL7jAY",
                "name": "truncated_video",
                "end_time": 10.0,
            }
        )
        self.store.create_child(
            self.user.id, self.vert_loc, 'poll_question', fields={
                "name": "T1_changemind_poll_foo_2",
                "display_name": "Change your answer",
                "reset": False,
                "question": "Have you changed your mind?",
                "answers": [{"id": "yes", "text": "Yes"}, {"id": "no", "text": "No"}],
            }
        )
        self.course = self.store.publish(self.course.location, self.user.id)

    def check_components_on_page(self, component_types, expected_types):
        """
        Ensure that the right types end up on the page.

        component_types is the list of advanced components.

        expected_types is the list of elements that should appear on the page.

        expected_types and component_types should be similar, but not
        exactly the same -- for example, 'video' in
        component_types should cause 'Video' to be present.
        """
        self.course.advanced_modules = component_types
        self.store.update_item(self.course, self.user.id)

        # just pick one vertical
        resp = self.client.get_html(get_url('container_handler', self.vert_loc))
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
        # just pick one vertical
        usage_key = self.course.id.make_usage_key('vertical', None)

        resp = self.client.get_html(get_url('container_handler', usage_key))
        self.assertEqual(resp.status_code, 400)

    def test_edit_unit(self):
        """Verifies rendering the editor in all the verticals in the given test course"""
        self._check_verticals([self.vert_loc])

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
        self.store.convert_to_draft(self.problem.location, self.user.id)

        # Query get_items() and find the html item. This should just return back a single item (not 2).
        direct_store_items = self.store.get_items(
            self.course.id, revision=ModuleStoreEnum.RevisionOption.published_only
        )
        items_from_direct_store = [item for item in direct_store_items if (item.location == self.problem.location)]
        self.assertEqual(len(items_from_direct_store), 1)
        self.assertFalse(getattr(items_from_direct_store[0], 'is_draft', False))

        # Fetch from the draft store.
        draft_store_items = self.store.get_items(
            self.course.id, revision=ModuleStoreEnum.RevisionOption.draft_only
        )
        items_from_draft_store = [item for item in draft_store_items if (item.location == self.problem.location)]
        self.assertEqual(len(items_from_draft_store), 1)
        # TODO the below won't work for split mongo
        self.assertTrue(getattr(items_from_draft_store[0], 'is_draft', False))

    def test_draft_metadata(self):
        '''
        This verifies a bug we had where inherited metadata was getting written to the
        module as 'own-metadata' when publishing. Also verifies the metadata inheritance is
        properly computed
        '''
        # refetch course so it has all the children correct
        course = self.store.update_item(self.course, self.user.id)
        course.graceperiod = timedelta(days=1, hours=5, minutes=59, seconds=59)
        course = self.store.update_item(course, self.user.id)
        problem = self.store.get_item(self.problem.location)

        self.assertEqual(problem.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(problem))

        self.store.convert_to_draft(problem.location, self.user.id)

        # refetch to check metadata
        problem = self.store.get_item(problem.location)

        self.assertEqual(problem.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(problem))

        # publish module
        self.store.publish(problem.location, self.user.id)

        # refetch to check metadata
        problem = self.store.get_item(problem.location)

        self.assertEqual(problem.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(problem))

        # put back in draft and change metadata and see if it's now marked as 'own_metadata'
        self.store.convert_to_draft(problem.location, self.user.id)
        problem = self.store.get_item(problem.location)

        new_graceperiod = timedelta(hours=1)

        self.assertNotIn('graceperiod', own_metadata(problem))
        problem.graceperiod = new_graceperiod
        # Save the data that we've just changed to the underlying
        # MongoKeyValueStore before we update the mongo datastore.
        problem.save()
        self.assertIn('graceperiod', own_metadata(problem))
        self.assertEqual(problem.graceperiod, new_graceperiod)

        self.store.update_item(problem, self.user.id)

        # read back to make sure it reads as 'own-metadata'
        problem = self.store.get_item(problem.location)

        self.assertIn('graceperiod', own_metadata(problem))
        self.assertEqual(problem.graceperiod, new_graceperiod)

        # republish
        self.store.publish(problem.location, self.user.id)

        # and re-read and verify 'own-metadata'
        self.store.convert_to_draft(problem.location, self.user.id)
        problem = self.store.get_item(problem.location)

        self.assertIn('graceperiod', own_metadata(problem))
        self.assertEqual(problem.graceperiod, new_graceperiod)

    def test_get_depth_with_drafts(self):
        # make sure no draft items have been returned
        num_drafts = self._get_draft_counts(self.course)
        self.assertEqual(num_drafts, 0)

        # put into draft
        self.store.convert_to_draft(self.problem.location, self.user.id)

        # make sure we can query that item and verify that it is a draft
        draft_problem = self.store.get_item(self.problem.location)
        self.assertTrue(getattr(draft_problem, 'is_draft', False))

        # now requery with depth
        course = self.store.get_course(self.course.id, depth=None)

        # make sure just one draft item have been returned
        num_drafts = self._get_draft_counts(course)
        self.assertEqual(num_drafts, 1)

    @mock.patch('xmodule.course_module.requests.get')
    def test_import_textbook_as_content_element(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()
        self.course.textbooks = [Textbook("Textbook", "https://s3.amazonaws.com/edx-textbooks/guttag_computation_v3/")]
        course = self.store.update_item(self.course, self.user.id)
        self.assertGreater(len(course.textbooks), 0)

    def test_import_polls(self):
        items = self.store.get_items(self.course.id, qualifiers={'category': 'poll_question'})
        self.assertTrue(len(items) > 0)
        # check that there's actually content in the 'question' field
        self.assertGreater(len(items[0].question), 0)

    def test_module_preview_in_whitelist(self):
        """
        Tests the ajax callback to render an XModule
        """
        with override_settings(COURSES_WITH_UNSAFE_CODE=[unicode(self.course.id)]):
            # also try a custom response which will trigger the 'is this course in whitelist' logic
            resp = self.client.get_json(
                get_url('xblock_view_handler', self.vert_loc, kwargs={'view_name': 'container_preview'})
            )
            self.assertEqual(resp.status_code, 200)

            vertical = self.store.get_item(self.vert_loc)
            for child in vertical.children:
                self.assertContains(resp, unicode(child))

    def test_delete(self):
        # make sure the parent points to the child object which is to be deleted
        # need to refetch chapter b/c at the time it was assigned it had no children
        chapter = self.store.get_item(self.chapter_loc)
        self.assertIn(self.seq_loc, chapter.children)

        self.client.delete(get_url('xblock_handler', self.seq_loc))

        with self.assertRaises(ItemNotFoundError):
            self.store.get_item(self.seq_loc)

        chapter = self.store.get_item(self.chapter_loc)

        # make sure the parent no longer points to the child object which was deleted
        self.assertNotIn(self.seq_loc, chapter.children)

    def test_asset_delete_and_restore(self):
        '''
        This test will exercise the soft delete/restore functionality of the assets
        '''
        asset_key = self._delete_asset_in_course()

        # now try to find it in store, but they should not be there any longer
        content = contentstore().find(asset_key, throw_on_not_found=False)
        self.assertIsNone(content)

        # now try to find it and the thumbnail in trashcan - should be in there
        content = contentstore('trashcan').find(asset_key, throw_on_not_found=False)
        self.assertIsNotNone(content)

        # let's restore the asset
        restore_asset_from_trashcan(unicode(asset_key))

        # now try to find it in courseware store, and they should be back after restore
        content = contentstore('trashcan').find(asset_key, throw_on_not_found=False)
        self.assertIsNotNone(content)

    def _delete_asset_in_course(self):
        """
        Helper method for:
          1) importing course from xml
          2) finding asset in course (verifying non-empty)
          3) computing thumbnail location of asset
          4) deleting the asset from the course
        """
        asset_key = self.course.id.make_asset_key('asset', 'sample_static.txt')
        content = StaticContent(
            asset_key, "Fake asset", "application/text", "test",
        )
        contentstore().save(content)

        # go through the website to do the delete, since the soft-delete logic is in the view
        url = reverse_course_url(
            'assets_handler',
            self.course.id,
            kwargs={'asset_key_string': unicode(asset_key)}
        )
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        return asset_key

    def test_empty_trashcan(self):
        '''
        This test will exercise the emptying of the asset trashcan
        '''
        self._delete_asset_in_course()

        # make sure there's something in the trashcan
        all_assets, __ = contentstore('trashcan').get_all_content_for_course(self.course.id)
        self.assertGreater(len(all_assets), 0)

        # empty the trashcan
        empty_asset_trashcan([self.course.id])

        # make sure trashcan is empty
        all_assets, count = contentstore('trashcan').get_all_content_for_course(self.course.id)
        self.assertEqual(len(all_assets), 0)
        self.assertEqual(count, 0)

    def test_illegal_draft_crud_ops(self):
        # this test presumes old mongo and split_draft not full split
        with self.assertRaises(InvalidVersionError):
            self.store.convert_to_draft(self.chapter_loc, self.user.id)

        chapter = self.store.get_item(self.chapter_loc)
        chapter.data = 'chapter data'
        self.store.update_item(chapter, self.user.id)
        newobject = self.store.get_item(self.chapter_loc)
        self.assertFalse(getattr(newobject, 'is_draft', False))

        with self.assertRaises(InvalidVersionError):
            self.store.unpublish(self.chapter_loc, self.user.id)

    def test_bad_contentstore_request(self):
        resp = self.client.get_html('http://localhost:8001/c4x/CDX/123123/asset/&images_circuits_Lab7Solution2.png')
        self.assertEqual(resp.status_code, 400)

    def test_delete_course(self):
        """
        This test creates a course, makes a draft item, and deletes the course. This will also assert that the
        draft content is also deleted
        """
        # add an asset
        asset_key = self.course.id.make_asset_key('asset', 'sample_static.txt')
        content = StaticContent(
            asset_key, "Fake asset", "application/text", "test",
        )
        contentstore().save(content)
        assets, count = contentstore().get_all_content_for_course(self.course.id)
        self.assertGreater(len(assets), 0)
        self.assertGreater(count, 0)

        self.store.convert_to_draft(self.vert_loc, self.user.id)

        # delete the course
        self.store.delete_course(self.course.id, self.user.id)

        # assert that there's absolutely no non-draft modules in the course
        # this should also include all draft items
        items = self.store.get_items(self.course.id)
        self.assertEqual(len(items), 0)

        # assert that all content in the asset library is also deleted
        assets, count = contentstore().get_all_content_for_course(self.course.id)
        self.assertEqual(len(assets), 0)
        self.assertEqual(count, 0)

    def test_course_handouts_rewrites(self):
        """
        Test that the xblock_handler rewrites static handout links
        """
        handouts = self.store.create_item(
            self.user.id, self.course.id, 'course_info', 'handouts', fields={
                "data": "<a href='/static/handouts/sample_handout.txt'>Sample</a>",
            }
        )

        # get module info (json)
        resp = self.client.get(get_url('xblock_handler', handouts.location))

        # make sure we got a successful response
        self.assertEqual(resp.status_code, 200)
        # check that /static/ has been converted to the full path
        # note, we know the link it should be because that's what in the 'toy' course in the test data
        asset_key = self.course.id.make_asset_key('asset', 'handouts_sample_handout.txt')
        self.assertContains(resp, unicode(asset_key))

    def test_prefetch_children(self):
        # make sure we haven't done too many round trips to DB
        # note we say 4 round trips here for:
        # 1) the course,
        # 2 & 3) for the chapters and sequentials
        # Because we're querying from the top of the tree, we cache information needed for inheritance,
        # so we don't need to make an extra query to compute it.
        # set the branch to 'publish' in order to prevent extra lookups of draft versions
        with self.store.branch_setting(ModuleStoreEnum.Branch.published_only, self.course.id):
            with check_mongo_calls(3, 0):
                course = self.store.get_course(self.course.id, depth=2)

            # make sure we pre-fetched a known sequential which should be at depth=2
            self.assertIn(self.seq_loc, course.system.module_data)

            # make sure we don't have a specific vertical which should be at depth=3
            self.assertNotIn(self.vert_loc, course.system.module_data)

        # Now, test with the branch set to draft. No extra round trips b/c it doesn't go deep enough to get
        # beyond direct only categories
        with self.store.branch_setting(ModuleStoreEnum.Branch.draft_preferred, self.course.id):
            with check_mongo_calls(3, 0):
                self.store.get_course(self.course.id, depth=2)

    def _check_verticals(self, locations):
        """ Test getting the editing HTML for each vertical. """
        # Assert is here to make sure that the course being tested actually has verticals (units) to check.
        self.assertGreater(len(locations), 0)
        for loc in locations:
            resp = self.client.get_html(get_url('container_handler', loc))
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
        self.assert_course_creation_failed(r"(?s)Unable to create course 'Robot Super Course'.*")

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
        course = CourseFactory.create()
        resp = self._show_course_overview(course.id)
        self.assertContains(
            resp,
            '<article class="outline outline-complex outline-course" data-locator="{locator}" data-course-key="{course_key}">'.format(
                locator=unicode(course.location),
                course_key=unicode(course.id),
            ),
            status_code=200,
            html=True
        )

    def test_create_item(self):
        """Test creating a new xblock instance."""
        course = CourseFactory.create()

        section_data = {
            'parent_locator': unicode(course.location),
            'category': 'chapter',
            'display_name': 'Section One',
        }

        resp = self.client.ajax_post(reverse_url('xblock_handler'), section_data)

        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        retarget = unicode(course.id.make_usage_key('chapter', 'REPLACE')).replace('REPLACE', r'([0-9]|[a-f]){3,}')
        self.assertRegexpMatches(data['locator'], retarget)

    def test_capa_module(self):
        """Test that a problem treats markdown specially."""
        course = CourseFactory.create()

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

        course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['simple'])
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

        # go look at the Edit page
        unit_key = course_key.make_usage_key('vertical', 'test_vertical')
        resp = self.client.get_html(get_url('container_handler', unit_key))
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
        course = CourseFactory.create()

        # crate a new module and add it as a child to a vertical
        new_discussion_item = self.store.create_item(self.user.id, course.id, 'discussion', 'new_component')

        self.assertNotEquals(new_discussion_item.discussion_id, '$$GUID$$')

    def test_metadata_inheritance(self):
        course_items = import_from_xml(self.store, self.user.id, 'common/test/data/', ['toy'])

        course = course_items[0]
        verticals = self.store.get_items(course.id, qualifiers={'category': 'vertical'})

        # let's assert on the metadata_inheritance on an existing vertical
        for vertical in verticals:
            self.assertEqual(course.xqa_key, vertical.xqa_key)
            self.assertEqual(course.start, vertical.start)

        self.assertGreater(len(verticals), 0)

        # crate a new module and add it as a child to a vertical
        parent = verticals[0]
        new_block = self.store.create_child(
            self.user.id, parent.location, 'html', 'new_component'
        )

        # flush the cache
        new_block = self.store.get_item(new_block.location)

        # check for grace period definition which should be defined at the course level
        self.assertEqual(parent.graceperiod, new_block.graceperiod)
        self.assertEqual(parent.start, new_block.start)
        self.assertEqual(course.start, new_block.start)

        self.assertEqual(course.xqa_key, new_block.xqa_key)

        #
        # now let's define an override at the leaf node level
        #
        new_block.graceperiod = timedelta(1)
        self.store.update_item(new_block, self.user.id)

        # flush the cache and refetch
        new_block = self.store.get_item(new_block.location)

        self.assertEqual(timedelta(1), new_block.graceperiod)

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
        courses = import_from_xml(
            self.store,
            self.user.id,
            'common/test/data/',
            ['conditional_and_poll'],
            static_content_store=content_store
        )

        course = courses[0]

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

    def test_course_handler_with_invalid_course_key_string(self):
        """Test viewing the course overview page with invalid course id"""

        response = self.client.get_html('/course/edX/test')
        self.assertEquals(response.status_code, 404)


class MetadataSaveTestCase(ContentStoreTestCase):
    """Test that metadata is correctly cached and decached."""

    def setUp(self):
        super(MetadataSaveTestCase, self).setUp()

        course = CourseFactory.create()

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


class RerunCourseTest(ContentStoreTestCase):
    """
    Tests for Rerunning a course via the view handler
    """
    def setUp(self):
        super(RerunCourseTest, self).setUp()
        self.destination_course_data = {
            'org': 'MITx',
            'number': '111',
            'display_name': 'Robot Super Course',
            'run': '2013_Spring'
        }

    def post_rerun_request(
            self, source_course_key, destination_course_data=None, response_code=200, expect_error=False
    ):
        """Create and send an ajax post for the rerun request"""

        # create data to post
        rerun_course_data = {'source_course_key': unicode(source_course_key)}
        if not destination_course_data:
            destination_course_data = self.destination_course_data
        rerun_course_data.update(destination_course_data)
        destination_course_key = _get_course_id(destination_course_data)

        # post the request
        course_url = get_url('course_handler', destination_course_key, 'course_key_string')
        response = self.client.ajax_post(course_url, rerun_course_data)

        # verify response
        self.assertEqual(response.status_code, response_code)
        if not expect_error:
            json_resp = parse_json(response)
            self.assertNotIn('ErrMsg', json_resp)
            destination_course_key = CourseKey.from_string(json_resp['destination_course_key'])
        return destination_course_key

    def get_course_listing_elements(self, html, course_key):
        """Returns the elements in the course listing section of html that have the given course_key"""
        return html.cssselect('.course-item[data-course-key="{}"]'.format(unicode(course_key)))

    def get_unsucceeded_course_action_elements(self, html, course_key):
        """Returns the elements in the unsucceeded course action section that have the given course_key"""
        return html.cssselect('.courses-processing li[data-course-key="{}"]'.format(unicode(course_key)))

    def assertInCourseListing(self, course_key):
        """
        Asserts that the given course key is in the accessible course listing section of the html
        and NOT in the unsucceeded course action section of the html.
        """
        course_listing = lxml.html.fromstring(self.client.get_html('/course/').content)
        self.assertEqual(len(self.get_course_listing_elements(course_listing, course_key)), 1)
        self.assertEqual(len(self.get_unsucceeded_course_action_elements(course_listing, course_key)), 0)

    def assertInUnsucceededCourseActions(self, course_key):
        """
        Asserts that the given course key is in the unsucceeded course action section of the html
        and NOT in the accessible course listing section of the html.
        """
        course_listing = lxml.html.fromstring(self.client.get_html('/course/').content)
        self.assertEqual(len(self.get_course_listing_elements(course_listing, course_key)), 0)
        self.assertEqual(len(self.get_unsucceeded_course_action_elements(course_listing, course_key)), 1)

    def verify_rerun_course(self, source_course_key, destination_course_key, destination_display_name):
        """
        Verify the contents of the course rerun action
        """
        rerun_state = CourseRerunState.objects.find_first(course_key=destination_course_key)
        expected_states = {
            'state': CourseRerunUIStateManager.State.SUCCEEDED,
            'display_name': destination_display_name,
            'source_course_key': source_course_key,
            'course_key': destination_course_key,
            'should_display': True,
        }
        for field_name, expected_value in expected_states.iteritems():
            self.assertEquals(getattr(rerun_state, field_name), expected_value)

        # Verify that the creator is now enrolled in the course.
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, destination_course_key))

        # Verify both courses are in the course listing section
        self.assertInCourseListing(source_course_key)
        self.assertInCourseListing(destination_course_key)

    def test_rerun_course_success(self):
        source_course = CourseFactory.create()
        destination_course_key = self.post_rerun_request(source_course.id)
        self.verify_rerun_course(source_course.id, destination_course_key, self.destination_course_data['display_name'])

    def test_rerun_of_rerun(self):
        source_course = CourseFactory.create()
        rerun_course_key = self.post_rerun_request(source_course.id)
        rerun_of_rerun_data = {
            'org': rerun_course_key.org,
            'number': rerun_course_key.course,
            'display_name': 'rerun of rerun',
            'run': 'rerun2'
        }
        rerun_of_rerun_course_key = self.post_rerun_request(rerun_course_key, rerun_of_rerun_data)
        self.verify_rerun_course(rerun_course_key, rerun_of_rerun_course_key, rerun_of_rerun_data['display_name'])

    def test_rerun_course_fail_no_source_course(self):
        with mock.patch.dict('django.conf.settings.FEATURES', {'ALLOW_COURSE_RERUNS': True}):
            existent_course_key = CourseFactory.create().id
            non_existent_course_key = CourseLocator("org", "non_existent_course", "non_existent_run")
            destination_course_key = self.post_rerun_request(non_existent_course_key)

            # Verify that the course rerun action is marked failed
            rerun_state = CourseRerunState.objects.find_first(course_key=destination_course_key)
            self.assertEquals(rerun_state.state, CourseRerunUIStateManager.State.FAILED)
            self.assertIn("Cannot find a course at", rerun_state.message)

            # Verify that the creator is not enrolled in the course.
            self.assertFalse(CourseEnrollment.is_enrolled(self.user, non_existent_course_key))

            # Verify that the existing course continues to be in the course listings
            self.assertInCourseListing(existent_course_key)

            # Verify that the failed course is NOT in the course listings
            self.assertInUnsucceededCourseActions(destination_course_key)

    def test_rerun_course_fail_duplicate_course(self):
        existent_course_key = CourseFactory.create().id
        destination_course_data = {
            'org': existent_course_key.org,
            'number': existent_course_key.course,
            'display_name': 'existing course',
            'run': existent_course_key.run
        }
        destination_course_key = self.post_rerun_request(
            existent_course_key, destination_course_data, expect_error=True
        )

        # Verify that the course rerun action doesn't exist
        with self.assertRaises(CourseActionStateItemNotFoundError):
            CourseRerunState.objects.find_first(course_key=destination_course_key)

        # Verify that the existing course continues to be in the course listing
        self.assertInCourseListing(existent_course_key)

    def test_rerun_with_permission_denied(self):
        with mock.patch.dict('django.conf.settings.FEATURES', {"ENABLE_CREATOR_GROUP": True}):
            source_course = CourseFactory.create()
            auth.add_users(self.user, CourseCreatorRole(), self.user)
            self.user.is_staff = False
            self.user.save()
            self.post_rerun_request(source_course.id, response_code=403, expect_error=True)

    def test_rerun_error(self):
        error_message = "Mock Error Message"
        with mock.patch(
                'xmodule.modulestore.mixed.MixedModuleStore.clone_course',
                mock.Mock(side_effect=Exception(error_message))
        ):
            source_course = CourseFactory.create()
            destination_course_key = self.post_rerun_request(source_course.id)
            rerun_state = CourseRerunState.objects.find_first(course_key=destination_course_key)
            self.assertEquals(rerun_state.state, CourseRerunUIStateManager.State.FAILED)
            self.assertIn(error_message, rerun_state.message)


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


def _get_course_id(course_data, key_class=SlashSeparatedCourseKey):
    """Returns the course ID (org/number/run)."""
    return key_class(course_data['org'], course_data['number'], course_data['run'])
