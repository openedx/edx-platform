#pylint: disable=E1101

import mock
import shutil

from textwrap import dedent

from django.test.utils import override_settings
from django.conf import settings
from path import path
from tempdir import mkdtemp_clean
from fs.osfs import OSFS
import copy
from json import loads
from datetime import timedelta
from django.test import TestCase

from django.contrib.auth.models import User
from django.dispatch import Signal
from contentstore.utils import get_modulestore
from contentstore.tests.utils import parse_json, AjaxEnabledTestClient

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from contentstore.tests.modulestore_config import TEST_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from xmodule.modulestore import Location, mongo
from xmodule.modulestore.keys import CourseKey
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
from xmodule.modulestore.locator import BlockUsageLocator

from contentstore.views.component import ADVANCED_COMPONENT_TYPES
from xmodule.exceptions import NotFoundError

from django_comment_common.utils import are_permissions_roles_seeded
from xmodule.exceptions import InvalidVersionError
from uuid import uuid4
from pymongo import MongoClient
from student.models import CourseEnrollment
import re

from contentstore.utils import delete_course_and_groups
from xmodule.modulestore.django import loc_mapper
from student.roles import CourseCreatorRole
from student import auth
from xmodule.modulestore.locations import SlashSeparatedCourseKey

TEST_DATA_CONTENTSTORE = copy.deepcopy(settings.CONTENTSTORE)
TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'] = 'test_xcontent_%s' % uuid4().hex


class MongoCollectionFindWrapper(object):
    def __init__(self, original):
        self.original = original
        self.counter = 0

    def find(self, query, *args, **kwargs):
        self.counter = self.counter + 1
        return self.original(query, *args, **kwargs)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class ContentStoreToyCourseTest(ModuleStoreTestCase):
    """
    Tests that rely on the toy courses.
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

        self.client = AjaxEnabledTestClient()
        self.client.login(username=uname, password=password)

    def tearDown(self):
        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'])
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
        store = modulestore('direct')
        import_from_xml(store, 'common/test/data/', ['simple'])

        course_id = 'edX/simple/2012_Fall'
        course = store.get_course(CourseKey.from_string(course_id))

        course.advanced_modules = component_types

        store.update_item(course, self.user.id)

        # just pick one vertical
        descriptor = store.get_items(CourseKey.from_string(course.id), category='vertical',)
        locator = loc_mapper().translate_location(course.location.course_id, descriptor.location, True, True)
        resp = self.client.get_html(locator.url_reverse('unit'))
        self.assertEqual(resp.status_code, 200)
        _test_no_locations(self, resp)

        for expected in expected_types:
            self.assertIn(expected, resp.content)

    def test_advanced_components_in_edit_unit(self):
        # This could be made better, but for now let's just assert that we see the advanced modules mentioned in the page
        # response HTML
        self.check_components_on_page(
            ADVANCED_COMPONENT_TYPES,
            ['Word cloud', 'Annotation', 'Text Annotation', 'Video Annotation',
             'Open Response Assessment', 'Peer Grading Interface'],
        )

    def test_advanced_components_require_two_clicks(self):
        self.check_components_on_page(['word_cloud'], ['Word cloud'])

    def test_malformed_edit_unit_request(self):
        store = modulestore('direct')
        import_from_xml(store, 'common/test/data/', ['simple'])

        # just pick one vertical
        descriptor = store.get_items(Location('i4x', 'edX', 'simple', 'vertical', None, None))[0]
        location = descriptor.location.replace(name='.' + descriptor.location.name)
        locator = loc_mapper().translate_location(location, add_entry_if_missing=True)

        resp = self.client.get_html(locator.url_reverse('unit'))
        self.assertEqual(resp.status_code, 400)
        _test_no_locations(self, resp, status_code=400)

    def check_edit_unit(self, test_course_name):
        _, course_items = import_from_xml(modulestore('direct'), 'common/test/data/', [test_course_name])

        items = modulestore().get_items(Location('i4x', 'edX', test_course_name, 'vertical', None, None))
        self._check_verticals(items, course_items[0].id)

    def _lock_an_asset(self, content_store, course_id):
        """
        Lock an arbitrary asset in the course
        :param course_location:
        """
        course_assets, __ = content_store.get_all_content_for_course(course_id)
        self.assertGreater(len(course_assets), 0, "No assets to lock")
        content_store.set_attr(course_assets[0], 'locked', True)
        return course_assets[0]

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
        store = modulestore('direct')
        draft_store = modulestore('draft')
        import_from_xml(store, 'common/test/data/', ['simple'])

        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        draft_store.convert_to_draft(html_module.location)

        # now query get_items() to get this location with revision=None, this should just
        # return back a single item (not 2)

        items = store.get_items(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))
        self.assertEqual(len(items), 1)
        self.assertFalse(getattr(items[0], 'is_draft', False))

        # now refetch from the draft store. Note that even though we pass
        # None in the revision field, the draft store will replace that with 'draft'
        items = draft_store.get_items(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))
        self.assertEqual(len(items), 1)
        self.assertTrue(getattr(items[0], 'is_draft', False))

    def test_draft_metadata(self):
        '''
        This verifies a bug we had where inherited metadata was getting written to the
        module as 'own-metadata' when publishing. Also verifies the metadata inheritance is
        properly computed
        '''
        store = modulestore('direct')
        draft_store = modulestore('draft')
        import_from_xml(store, 'common/test/data/', ['simple'])

        course = draft_store.get_item(Location('i4x', 'edX', 'simple',
                                               'course', '2012_Fall', None), depth=None)
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        draft_store.convert_to_draft(html_module.location)

        # refetch to check metadata
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        # publish module
        draft_store.publish(html_module.location, 0)

        # refetch to check metadata
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        self.assertEqual(html_module.graceperiod, course.graceperiod)
        self.assertNotIn('graceperiod', own_metadata(html_module))

        # put back in draft and change metadata and see if it's now marked as 'own_metadata'
        draft_store.convert_to_draft(html_module.location)
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

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
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        self.assertIn('graceperiod', own_metadata(html_module))
        self.assertEqual(html_module.graceperiod, new_graceperiod)

        # republish
        draft_store.publish(html_module.location, 0)

        # and re-read and verify 'own-metadata'
        draft_store.convert_to_draft(html_module.location)
        html_module = draft_store.get_item(Location('i4x', 'edX', 'simple', 'html', 'test_html', None))

        self.assertIn('graceperiod', own_metadata(html_module))
        self.assertEqual(html_module.graceperiod, new_graceperiod)

    def test_get_depth_with_drafts(self):
        import_from_xml(modulestore('direct'), 'common/test/data/', ['simple'])

        course = modulestore('draft').get_item(
            Location('i4x', 'edX', 'simple', 'course', '2012_Fall', None),
            depth=None
        )

        # make sure no draft items have been returned
        num_drafts = self._get_draft_counts(course)
        self.assertEqual(num_drafts, 0)

        problem = modulestore('draft').get_item(
            Location('i4x', 'edX', 'simple', 'problem', 'ps01-simple', None)
        )

        # put into draft
        modulestore('draft').convert_to_draft(problem.location)

        # make sure we can query that item and verify that it is a draft
        draft_problem = modulestore('draft').get_item(
            Location('i4x', 'edX', 'simple', 'problem', 'ps01-simple', None)
        )
        self.assertTrue(getattr(draft_problem, 'is_draft', False))

        # now requery with depth
        course = modulestore('draft').get_item(
            Location('i4x', 'edX', 'simple', 'course', '2012_Fall', None),
            depth=None
        )

        # make sure just one draft item have been returned
        num_drafts = self._get_draft_counts(course)
        self.assertEqual(num_drafts, 1)

    def test_no_static_link_rewrites_on_import(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        handouts = module_store.get_item(Location('i4x', 'edX', 'toy', 'course_info', 'handouts', None))
        self.assertIn('/static/', handouts.data)

        handouts = module_store.get_item(Location('i4x', 'edX', 'toy', 'html', 'toyhtml', None))
        self.assertIn('/static/', handouts.data)

    @mock.patch('xmodule.course_module.requests.get')
    def test_import_textbook_as_content_element(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        course = module_store.get_item(Location('i4x', 'edX', 'toy', 'course', '2012_Fall', None))

        self.assertGreater(len(course.textbooks), 0)

    def test_default_tabs_on_create_course(self):
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')
        course_location = Location('i4x', 'edX', '999', 'course', 'Robot_Super_Course', None)

        course = module_store.get_item(course_location)

        expected_tabs = []
        expected_tabs.append({u'type': u'courseware'})
        expected_tabs.append({u'type': u'course_info', u'name': u'Course Info'})
        expected_tabs.append({u'type': u'textbooks'})
        expected_tabs.append({u'type': u'discussion', u'name': u'Discussion'})
        expected_tabs.append({u'type': u'wiki', u'name': u'Wiki'})
        expected_tabs.append({u'type': u'progress', u'name': u'Progress'})

        self.assertEqual(course.tabs, expected_tabs)

    def test_create_static_tab_and_rename(self):
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')
        course_location = Location('i4x', 'edX', '999', 'course', 'Robot_Super_Course', None)

        item = ItemFactory.create(parent_location=course_location, category='static_tab', display_name="My Tab")

        course = module_store.get_item(course_location)

        expected_tabs = []
        expected_tabs.append({u'type': u'courseware'})
        expected_tabs.append({u'type': u'course_info', u'name': u'Course Info'})
        expected_tabs.append({u'type': u'textbooks'})
        expected_tabs.append({u'type': u'discussion', u'name': u'Discussion'})
        expected_tabs.append({u'type': u'wiki', u'name': u'Wiki'})
        expected_tabs.append({u'type': u'progress', u'name': u'Progress'})
        expected_tabs.append({u'type': u'static_tab', u'name': u'My Tab', u'url_slug': u'My_Tab'})

        self.assertEqual(course.tabs, expected_tabs)

        item.display_name = 'Updated'
        module_store.update_item(item, self.user.id)

        course = module_store.get_item(course_location)

        expected_tabs = []
        expected_tabs.append({u'type': u'courseware'})
        expected_tabs.append({u'type': u'course_info', u'name': u'Course Info'})
        expected_tabs.append({u'type': u'textbooks'})
        expected_tabs.append({u'type': u'discussion', u'name': u'Discussion'})
        expected_tabs.append({u'type': u'wiki', u'name': u'Wiki'})
        expected_tabs.append({u'type': u'progress', u'name': u'Progress'})
        expected_tabs.append({u'type': u'static_tab', u'name': u'Updated', u'url_slug': u'My_Tab'})

        self.assertEqual(course.tabs, expected_tabs)

    def test_static_tab_reordering(self):
        module_store, course_location, new_location = self._create_static_tabs()

        course = module_store.get_item(course_location)

        # reverse the ordering
        reverse_tabs = []
        for tab in course.tabs:
            if tab['type'] == 'static_tab':
                reverse_tabs.insert(0, unicode(self._get_tab_locator(course, tab)))

        self.client.ajax_post(new_location.url_reverse('tabs'), {'tabs': reverse_tabs})

        course = module_store.get_item(course_location)

        # compare to make sure that the tabs information is in the expected order after the server call
        course_tabs = []
        for tab in course.tabs:
            if tab['type'] == 'static_tab':
                course_tabs.append(unicode(self._get_tab_locator(course, tab)))

        self.assertEqual(reverse_tabs, course_tabs)

    def test_static_tab_deletion(self):
        module_store, course_location, _ = self._create_static_tabs()

        course = module_store.get_item(course_location)
        num_tabs = len(course.tabs)
        last_tab = course.tabs[-1]
        url_slug = last_tab['url_slug']
        delete_url = self._get_tab_locator(course, last_tab).url_reverse('xblock')

        self.client.delete(delete_url)

        course = module_store.get_item(course_location)
        self.assertEqual(num_tabs - 1, len(course.tabs))

        def tab_matches(tab):
            """ Checks if the tab matches the one we deleted """
            return tab['type'] == 'static_tab' and tab['url_slug'] == url_slug

        tab_found = any(tab_matches(tab) for tab in course.tabs)

        self.assertFalse(tab_found, "tab should have been deleted")

    def _get_tab_locator(self, course, tab):
        """ Returns the locator for a given tab. """
        tab_location = 'i4x://edX/999/static_tab/{0}'.format(tab['url_slug'])
        return loc_mapper().translate_location(Location(tab_location), True, True)

    def _create_static_tabs(self):
        """ Creates two static tabs in a dummy course. """
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')
        course_location = Location('i4x', 'edX', '999', 'course', 'Robot_Super_Course', None)
        new_location = loc_mapper().translate_location(course_location, True, True)

        ItemFactory.create(
            parent_location=course_location,
            category="static_tab",
            display_name="Static_1")
        ItemFactory.create(
            parent_location=course_location,
            category="static_tab",
            display_name="Static_2")

        return module_store, course_location, new_location

    def test_import_polls(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        items = module_store.get_items(Location('i4x', 'edX', 'toy', 'poll_question', None, None))
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
        resp = self._test_preview(Location('i4x', 'edX', 'toy', 'vertical', 'vertical_test', None), 'container_preview')
        # These are the data-ids of the xblocks contained in the vertical.
        # Ultimately, these must be converted to new locators.
        self.assertContains(resp, 'i4x://edX/toy/video/sample_video')
        self.assertContains(resp, 'i4x://edX/toy/video/separate_file_video')
        self.assertContains(resp, 'i4x://edX/toy/video/video_with_end_time')
        self.assertContains(resp, 'i4x://edX/toy/poll_question/T1_changemind_poll_foo_2')

    def _test_preview(self, location, view_name):
        """ Preview test case. """
        direct_store = modulestore('direct')
        import_from_xml(direct_store, 'common/test/data/', ['toy'])

        # also try a custom response which will trigger the 'is this course in whitelist' logic
        locator = loc_mapper().translate_location(location, True, True)
        resp = self.client.get_json(locator.url_reverse('xblock', view_name))
        self.assertEqual(resp.status_code, 200)
        # TODO: uncomment when preview no longer has locations being returned.
        # _test_no_locations(self, resp)
        return resp

    def test_delete(self):
        direct_store = modulestore('direct')
        course = CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')

        chapterloc = ItemFactory.create(parent_location=course.location, display_name="Chapter").location
        ItemFactory.create(parent_location=chapterloc, category='sequential', display_name="Sequential")

        sequential = direct_store.get_item(Location('i4x', 'edX', '999', 'sequential', 'Sequential', None))
        chapter = direct_store.get_item(Location('i4x', 'edX', '999', 'chapter', 'Chapter', None))

        # make sure the parent points to the child object which is to be deleted
        self.assertTrue(sequential.location.url() in chapter.children)

        location = loc_mapper().translate_location(sequential.location, True, True)
        self.client.delete(location.url_reverse('xblock'), {'recurse': True, 'all_versions': True})

        found = False
        try:
            direct_store.get_item(Location(['i4x', 'edX', '999', 'sequential', 'Sequential', None]))
            found = True
        except ItemNotFoundError:
            pass

        self.assertFalse(found)

        chapter = direct_store.get_item(Location(['i4x', 'edX', '999', 'chapter', 'Chapter', None]))

        # make sure the parent no longer points to the child object which was deleted
        self.assertFalse(sequential.location.url() in chapter.children)

    def test_about_overrides(self):
        '''
        This test case verifies that a course can use specialized override for about data, e.g. /about/Fall_2012/effort.html
        while there is a base definition in /about/effort.html
        '''
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])
        effort = module_store.get_item(Location(['i4x', 'edX', 'toy', 'about', 'effort', None]))
        self.assertEqual(effort.data, '6 hours')

        # this one should be in a non-override folder
        effort = module_store.get_item(Location(['i4x', 'edX', 'toy', 'about', 'end_date', None]))
        self.assertEqual(effort.data, 'TBD')

    def test_remove_hide_progress_tab(self):
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')
        course_location = Location(['i4x', 'edX', '999', 'course', 'Robot_Super_Course', None])
        course = module_store.get_item(course_location)
        self.assertFalse(course.hide_progress_tab)

    def test_asset_import(self):
        '''
        This test validates that an image asset is imported and a thumbnail was generated for a .gif
        '''
        content_store = contentstore()

        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store, verbose=True)

        course = module_store.get_course(CourseKey.from_string('edX/toy/2012_Fall'))

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
            location = StaticContent.get_location_from_path('/c4x/edX/toy/asset/sample_static.txt')
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
        content_store, trash_store, thumbnail_location = self._delete_asset_in_course()
        asset_location = StaticContent.get_location_from_path('/c4x/edX/toy/asset/sample_static.txt')

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
        module_store = modulestore('direct')
        _, course_items = import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store)

        # look up original (and thumbnail) in content store, should be there after import
        location = StaticContent.get_location_from_path('/c4x/edX/toy/asset/sample_static.txt')
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
        location = loc_mapper().translate_location(course.location, True, True)
        url = location.url_reverse('assets/', '/c4x/edX/toy/asset/sample_static.txt')
        resp = self.client.delete(url)
        self.assertEqual(resp.status_code, 204)

        return content_store, trash_store, thumbnail_location

    def test_course_info_updates_import_export(self):
        """
        Test that course info updates are imported and exported with all content fields ('data', 'items')
        """
        content_store = contentstore()
        module_store = modulestore('direct')
        data_dir = "common/test/data/"
        import_from_xml(module_store, data_dir, ['course_info_updates'],
                        static_content_store=content_store, verbose=True)

        course_id = CourseKey.from_string('edX/course_info_updates/2014_T1')
        course = module_store.get_item(course_id)

        self.assertIsNotNone(course)

        course_updates = module_store.get_item(
            Location(['i4x', 'edX', 'course_info_updates', 'course_info', 'updates', None]))

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
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_export')

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
        _, trash_store, _ = self._delete_asset_in_course()

        # make sure there's something in the trashcan
        course_id = CourseKey.from_string('edX/toy/6.002_Spring_2012')
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

    def test_clone_course(self):

        course_data = {
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            'run': '2013_Spring',
        }

        module_store = modulestore('direct')
        draft_store = modulestore('draft')
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        source_course_id = SlashSeparatedCourseKey.from_string('edX/toy/2012_Fall')
        dest_course_id = _get_course_id(course_data)

        # get a vertical (and components in it) to put into 'draft'
        # this is to assert that draft content is also cloned over
        vertical = module_store.get_item(
            source_course_id.make_usage_key('vertical', 'vertical_test'),
            depth=1
        )

        draft_store.convert_to_draft(vertical.location)
        for child in vertical.get_children():
            draft_store.convert_to_draft(child.location)

        items = module_store.get_items(source_course_id, qualifiers={'version': 'draft'})
        self.assertGreater(len(items), 0)

        _create_course(self, dest_course_id, course_data)

        content_store = contentstore()

        # now do the actual cloning
        clone_course(module_store, content_store, source_course_id, dest_course_id)

        # first assert that all draft content got cloned as well
        items = module_store.get_items(source_course_id, qualifiers={'version': 'draft'})
        self.assertGreater(len(items), 0)
        clone_items = module_store.get_items(dest_course_id, qualifiers={'version': 'draft'})
        self.assertGreater(len(clone_items), 0)
        self.assertEqual(len(items), len(clone_items))

        # now loop through all the units in the course and verify that the clone can render them, which
        # means the objects are at least present
        items = module_store.get_items(source_course_id, qualifiers={'version': None})
        self.assertGreater(len(items), 0)
        clone_items = module_store.get_items(dest_course_id, qualifiers={'version': None})
        self.assertGreater(len(clone_items), 0)

        for descriptor in items:
            source_item = module_store.get_item(descriptor.location)
            new_loc = descriptor.location.map_into_course(dest_course_id)
            print "Checking {0} should now also be at {1}".format(descriptor.location, new_loc)
            lookup_item = module_store.get_item(new_loc)

            if hasattr(source_item, 'data') and hasattr(lookup_item, 'data'):
                self.assertEqual(source_item.data, lookup_item.data)

            # also make sure that metadata was cloned over and filtered with own_metadata, i.e. inherited
            # values were not explicitly set
            self.assertEqual(own_metadata(source_item), own_metadata(lookup_item))

            # check that the children are as expected
            self.assertEqual(source_item.has_children, lookup_item.has_children)
            if source_item.has_children:
                expected_children = []
                for child_loc in source_item.children:
                    child_loc = child_loc.map_into_course(dest_course_id)
                    expected_children.append(child_loc)
                self.assertEqual(expected_children, lookup_item.children)

    def test_portable_link_rewrites_during_clone_course(self):
        course_data = {
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            'run': '2013_Spring'
        }

        module_store = modulestore('direct')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'])

        source_course_id = CourseKey.from_string('edX/toy/2012_Fall')
        dest_course_id = _get_course_id(course_data)

        # let's force a non-portable link in the clone source
        # as a final check, make sure that any non-portable links are rewritten during cloning
        html_module = module_store.get_item(source_course_id.make_usage_key('html', 'nonportable'))

        self.assertIsInstance(html_module.data, basestring)
        new_data = html_module.data = html_module.data.replace('/static/', '/c4x/{0}/{1}/asset/'.format(
            source_course_id.org, source_course_id.run))
        module_store.update_item(html_module, self.user.id)

        html_module = module_store.get_item(html_module.location)
        self.assertEqual(new_data, html_module.data)

        # create the destination course
        _create_course(self, dest_course_id, course_data)

        # do the actual cloning
        clone_course(module_store, content_store, source_course_id, dest_course_id)

        # make sure that any non-portable links are rewritten during cloning
        html_module = module_store.get_item(dest_course_id.make_usage_key('html', 'nonportable'))

        self.assertIn('/static/foo.jpg', html_module.data)

    def test_illegal_draft_crud_ops(self):
        draft_store = modulestore('draft')
        direct_store = modulestore('direct')

        course = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        location = Location('i4x://MITx/999/chapter/neuvo')
        # Ensure draft mongo store does not allow us to create chapters either directly or via convert to draft
        self.assertRaises(InvalidVersionError, draft_store.create_and_save_xmodule, location)
        direct_store.create_and_save_xmodule(location)
        self.assertRaises(InvalidVersionError, draft_store.convert_to_draft, location)
        chapter = draft_store.get_item(location)
        chapter.data = 'chapter data'

        with self.assertRaises(InvalidVersionError):
            draft_store.update_item(chapter, self.user.id)

        self.assertRaises(InvalidVersionError, draft_store.unpublish, location)

    def test_bad_contentstore_request(self):
        resp = self.client.get_html('http://localhost:8001/c4x/CDX/123123/asset/&images_circuits_Lab7Solution2.png')
        self.assertEqual(resp.status_code, 400)
        _test_no_locations(self, resp, 400)

    def test_rewrite_nonportable_links_on_import(self):
        module_store = modulestore('direct')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store)

        # first check a static asset link
        html_module_location = Location(['i4x', 'edX', 'toy', 'html', 'nonportable'])
        html_module = module_store.get_item(html_module_location)
        self.assertIn('/static/foo.jpg', html_module.data)

        # then check a intra courseware link
        html_module_location = Location(['i4x', 'edX', 'toy', 'html', 'nonportable_link'])
        html_module = module_store.get_item(html_module_location)
        self.assertIn('/jump_to_id/nonportable_link', html_module.data)

    def test_delete_course(self):
        """
        This test will import a course, make a draft item, and delete it. This will also assert that the
        draft content is also deleted
        """
        module_store = modulestore('direct')

        content_store = contentstore()
        draft_store = modulestore('draft')

        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store)

        course_id = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course').id

        # get a vertical (and components in it) to put into 'draft'
        vertical = module_store.get_item(Location(['i4x', 'edX', 'toy',
                                         'vertical', 'vertical_test', None]), depth=1)

        draft_store.convert_to_draft(vertical.location)
        for child in vertical.get_children():
            draft_store.convert_to_draft(child.location)

        # delete the course
        delete_course(module_store, content_store, course_id, commit=True)

        # assert that there's absolutely no non-draft modules in the course
        # this should also include all draft items
        items = module_store.get_items(course_id)
        self.assertEqual(len(items), 0)

        # assert that all content in the asset library is also deleted
        assets, count = content_store.get_all_content_for_course(course_id)
        self.assertEqual(len(assets), 0)
        self.assertEqual(count, 0)

    def verify_content_existence(self, store, root_dir, course_id, dirname, category_name, filename_suffix=''):
        filesystem = OSFS(root_dir / 'test_export')
        self.assertTrue(filesystem.exists(dirname))

        items = store.get_items(course_id, qualifiers={'category': category_name})

        for item in items:
            filesystem = OSFS(root_dir / ('test_export/' + dirname))
            self.assertTrue(filesystem.exists(item.location.name + filename_suffix))

    @mock.patch('xmodule.course_module.requests.get')
    def test_export_course(self, mock_get):
        mock_get.return_value.text = dedent("""
            <?xml version="1.0"?><table_of_contents>
            <entry page="5" page_label="ii" name="Table of Contents"/>
            </table_of_contents>
        """).strip()

        module_store = modulestore('direct')
        draft_store = modulestore('draft')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'], static_content_store=content_store)
        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        # get a vertical (and components in it) to copy into an orphan sub dag
        vertical = module_store.get_item(
            Location(['i4x', 'edX', 'toy', 'vertical', 'vertical_test', None]),
            depth=1
        )
        # We had a bug where orphaned draft nodes caused export to fail. This is here to cover that case.
        vertical.location = mongo.draft.as_draft(vertical.location.replace(name='no_references'))

        draft_store.update_item(vertical, allow_not_found=True)
        orphan_vertical = draft_store.get_item(vertical.location)
        self.assertEqual(orphan_vertical.location.name, 'no_references')

        # get the original vertical (and components in it) to put into 'draft'
        vertical = module_store.get_item(
            Location(['i4x', 'edX', 'toy', 'vertical', 'vertical_test', None]),
            depth=1)
        self.assertEqual(len(orphan_vertical.children), len(vertical.children))
        draft_store.convert_to_draft(vertical.location)
        for child in vertical.get_children():
            draft_store.convert_to_draft(child.location)

        root_dir = path(mkdtemp_clean())

        # now create a new/different private (draft only) vertical
        vertical.location = mongo.draft.as_draft(Location(['i4x', 'edX', 'toy', 'vertical', 'a_private_vertical', None]))
        draft_store.update_item(vertical, allow_not_found=True)
        private_vertical = draft_store.get_item(vertical.location)
        vertical = None  # blank out b/c i destructively manipulated its location 2 lines above

        # add the new private to list of children
        sequential = module_store.get_item(
            Location('i4x', 'edX', 'toy', 'sequential', 'vertical_sequential', None)
        )
        private_location_no_draft = private_vertical.location.replace(revision=None)
        sequential.children.append(private_location_no_draft.url())
        module_store.update_item(sequential, self.user.id)

        # read back the sequential, to make sure we have a pointer to
        sequential = module_store.get_item(Location(['i4x', 'edX', 'toy',
                                                     'sequential', 'vertical_sequential', None]))

        self.assertIn(private_location_no_draft.url(), sequential.children)

        locked_asset_key = self._lock_an_asset(content_store, course_id)
        locked_asset_attrs = content_store.get_attrs(locked_asset_key)
        # the later import will reupload
        del locked_asset_attrs['uploadDate']

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_export', draft_modulestore=draft_store)

        # check for static tabs
        self.verify_content_existence(module_store, root_dir, course_id, 'tabs', 'static_tab', '.html')

        # check for about content
        self.verify_content_existence(module_store, root_dir, course_id, 'about', 'about', '.html')

        # check for graiding_policy.json
        filesystem = OSFS(root_dir / 'test_export/policies/2012_Fall')
        self.assertTrue(filesystem.exists('grading_policy.json'))

        course = module_store.get_course(course_id)
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
        delete_course(module_store, content_store, course_id, commit=True)
        # reimport over old course
        self.check_import(
            module_store, root_dir, draft_store, content_store, course_id,
            locked_asset_key, locked_asset_attrs
        )
        # import to different course id
        self.check_import(
            module_store, root_dir, draft_store, content_store, CourseKey.from_string('anotherX/anotherToy/Someday'),
            locked_asset_key, locked_asset_attrs
        )

        shutil.rmtree(root_dir)

    def check_import(self, module_store, root_dir, draft_store, content_store, course_id,
                     locked_asset_key, locked_asset_attrs):
        # reimport
        import_from_xml(
            module_store,
            root_dir,
            ['test_export'],
            draft_store=draft_store,
            static_content_store=content_store,
            target_course_id=course_id,
        )

        items = module_store.get_items(course_id, qualifiers={'category': 'vertical'})
        self._check_verticals(items, course_id)

        # verify that we have the content in the draft store as well
        vertical = draft_store.get_item(
            course_id.make_usage_key('vertical', 'vertical_test'),
            depth=1
        )

        self.assertTrue(getattr(vertical, 'is_draft', False))
        self.assertNotIn('index_in_children_list', vertical.xml_attributes)
        self.assertNotIn('parent_sequential_url', vertical.xml_attributes)

        for child in vertical.get_children():
            self.assertTrue(getattr(child, 'is_draft', False))
            self.assertNotIn('index_in_children_list', child.xml_attributes)
            if hasattr(child, 'data'):
                self.assertNotIn('index_in_children_list', child.data)
            self.assertNotIn('parent_sequential_url', child.xml_attributes)
            if hasattr(child, 'data'):
                self.assertNotIn('parent_sequential_url', child.data)

        # make sure that we don't have a sequential that is in draft mode
        sequential = draft_store.get_item(
            course_id.make_usage_key('sequential', 'vertical_sequential')
        )

        self.assertFalse(getattr(sequential, 'is_draft', False))

        # verify that we have the private vertical
        test_private_vertical = draft_store.get_item(
            course_id.make_usage_key('vertical', 'a_private_vertical')
        )

        self.assertTrue(getattr(test_private_vertical, 'is_draft', False))

        # make sure the textbook survived the export/import
        course = module_store.get_course(course_id)

        self.assertGreater(len(course.textbooks), 0)

        locked_asset_key = locked_asset_key.map_into_course(course_id)
        new_attrs = content_store.get_attrs(locked_asset_key)
        for key, value in locked_asset_attrs.iteritems():
            if key == '_id':
                self.assertEqual(value['name'], new_attrs[key]['name'])
            elif key == 'filename':
                pass
            else:
                self.assertEqual(value, new_attrs[key])

    def test_export_course_with_metadata_only_video(self):
        module_store = modulestore('direct')
        draft_store = modulestore('draft')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'])
        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        # create a new video module and add it as a child to a vertical
        # this re-creates a bug whereby since the video template doesn't have
        # anything in 'data' field, the export was blowing up
        verticals = module_store.get_items(Location('i4x', 'edX', 'toy', 'vertical', None, None))

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        ItemFactory.create(parent_location=parent.location, category="video", display_name="untitled")

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_export', draft_modulestore=draft_store)

        shutil.rmtree(root_dir)

    def test_export_course_with_metadata_only_word_cloud(self):
        """
        Similar to `test_export_course_with_metadata_only_video`.
        """
        module_store = modulestore('direct')
        draft_store = modulestore('draft')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['word_cloud'])
        course_id = CourseKey.from_string('HarvardX/ER22x/2013_Spring')

        verticals = module_store.get_items(Location('i4x', 'HarvardX', 'ER22x', 'vertical', None, None))

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        ItemFactory.create(parent_location=parent.location, category="word_cloud", display_name="untitled")

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)

        # export out to a tempdir
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_export', draft_modulestore=draft_store)

        shutil.rmtree(root_dir)

    def test_empty_data_roundtrip(self):
        """
        Test that an empty `data` field is preserved through
        export/import.
        """
        module_store = modulestore('direct')
        draft_store = modulestore('draft')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'])
        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        verticals = module_store.get_items(Location('i4x', 'edX', 'toy', 'vertical', None, None))

        self.assertGreater(len(verticals), 0)

        parent = verticals[0]

        # Create a module, and ensure that its `data` field is empty
        word_cloud = ItemFactory.create(parent_location=parent.location, category="word_cloud", display_name="untitled")
        del word_cloud.data
        self.assertEquals(word_cloud.data, '')

        # Export the course
        root_dir = path(mkdtemp_clean())
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_roundtrip', draft_modulestore=draft_store)

        # Reimport and get the video back
        import_from_xml(module_store, root_dir)
        imported_word_cloud = module_store.get_item(Location('i4x', 'edX', 'toy', 'word_cloud', 'untitled', None))

        # It should now contain empty data
        self.assertEquals(imported_word_cloud.data, '')

    def test_html_export_roundtrip(self):
        """
        Test that a course which has HTML that has style formatting is preserved in export/import
        """
        module_store = modulestore('direct')
        content_store = contentstore()

        import_from_xml(module_store, 'common/test/data/', ['toy'])

        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        # Export the course
        root_dir = path(mkdtemp_clean())
        export_to_xml(module_store, content_store, course_id, root_dir, 'test_roundtrip')

        # Reimport and get the video back
        import_from_xml(module_store, root_dir)

        # get the sample HTML with styling information
        html_module = module_store.get_item(
            Location('i4x', 'edX', 'toy', 'html', 'with_styling')
        )
        self.assertIn('<p style="font:italic bold 72px/30px Georgia, serif; color: red; ">', html_module.data)

        # get the sample HTML with just a simple <img> tag information
        html_module = module_store.get_item(
            Location('i4x', 'edX', 'toy', 'html', 'just_img')
        )
        self.assertIn('<img src="/static/foo_bar.jpg" />', html_module.data)

    def test_course_handouts_rewrites(self):
        module_store = modulestore('direct')

        # import a test course
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        handout_location = Location(['i4x', 'edX', 'toy', 'course_info', 'handouts'])
        # get the translation
        handouts_locator = loc_mapper().translate_location(handout_location)

        # get module info (json)
        resp = self.client.get(handouts_locator.url_reverse('/xblock'))

        # make sure we got a successful response
        self.assertEqual(resp.status_code, 200)
        # check that /static/ has been converted to the full path
        # note, we know the link it should be because that's what in the 'toy' course in the test data
        self.assertContains(resp, '/c4x/edX/toy/asset/handouts_sample_handout.txt')

    def test_prefetch_children(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])
        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        wrapper = MongoCollectionFindWrapper(module_store.collection.find)
        module_store.collection.find = wrapper.find
        print module_store.metadata_inheritance_cache_subsystem
        print module_store.request_cache
        course = module_store.get_course(course_id, depth=2)

        # make sure we haven't done too many round trips to DB
        # note we say 3 round trips here for 1) the course, and 2 & 3) for the chapters and sequentials
        # Because we're querying from the top of the tree, we cache information needed for inheritance,
        # so we don't need to make an extra query to compute it.
        self.assertEqual(wrapper.counter, 3)

        # make sure we pre-fetched a known sequential which should be at depth=2
        self.assertTrue(Location(['i4x', 'edX', 'toy', 'sequential',
                                  'vertical_sequential', None]) in course.system.module_data)

        # make sure we don't have a specific vertical which should be at depth=3
        self.assertFalse(Location(['i4x', 'edX', 'toy', 'vertical', 'vertical_test', None])
                         in course.system.module_data)

    def test_export_course_without_content_store(self):
        module_store = modulestore('direct')
        content_store = contentstore()

        # Create toy course

        import_from_xml(module_store, 'common/test/data/', ['toy'])
        course_id = CourseKey.from_string('edX/toy/2012_Fall')

        root_dir = path(mkdtemp_clean())

        print 'Exporting to tempdir = {0}'.format(root_dir)
        export_to_xml(module_store, None, course_id, root_dir, 'test_export_no_content_store')

        # Delete the course from module store and reimport it

        delete_course(module_store, content_store, course_id, commit=True)

        import_from_xml(
            module_store, root_dir, ['test_export_no_content_store'],
            draft_store=None,
            static_content_store=None,
            target_course_id=course_id
        )

        # Verify reimported course

        items = module_store.get_items(
            course_id,
            qualifiers={'category': 'sequential', 'name': 'vertical_sequential'}
        )
        self.assertEqual(len(items), 1)

    def _check_verticals(self, items, course_id):
        """ Test getting the editing HTML for each vertical. """
        # Assert is here to make sure that the course being tested actually has verticals (units) to check.
        self.assertGreater(len(items), 0)
        for descriptor in items:
            unit_locator = loc_mapper().translate_location(descriptor.location, True, True)
            resp = self.client.get_html(unit_locator.url_reverse('unit'))
            self.assertEqual(resp.status_code, 200)
            _test_no_locations(self, resp)


@override_settings(CONTENTSTORE=TEST_DATA_CONTENTSTORE, MODULESTORE=TEST_MODULESTORE)
class ContentStoreTest(ModuleStoreTestCase):
    """
    Tests for the CMS ContentStore application.
    """
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
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

        self.client = AjaxEnabledTestClient()
        self.client.login(username=uname, password=password)

        self.course_data = {
            'org': 'MITx',
            'number': '999',
            'display_name': 'Robot Super Course',
            'run': '2013_Spring'
        }

    def tearDown(self):
        MongoClient().drop_database(TEST_DATA_CONTENTSTORE['DOC_STORE_CONFIG']['db'])
        _CONTENTSTORE.clear()

    def test_create_course(self):
        """Test new course creation - happy path"""
        self.assert_created_course()

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

    def test_create_course_check_forum_seeding(self):
        """Test new course creation and verify forum seeding """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        self.assertTrue(are_permissions_roles_seeded(_get_course_id(test_course_data)))

    def test_forum_unseeding_on_delete(self):
        """Test new course creation and verify forum unseeding """
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        course_id = _get_course_id(test_course_data)
        self.assertTrue(are_permissions_roles_seeded(course_id))
        delete_course_and_groups(course_id, commit=True)
        # should raise an exception for checking permissions on deleted course
        with self.assertRaises(ItemNotFoundError):
            are_permissions_roles_seeded(course_id)

    def test_forum_unseeding_with_multiple_courses(self):
        """Test new course creation and verify forum unseeding when there are multiple courses"""
        test_course_data = self.assert_created_course(number_suffix=uuid4().hex)
        second_course_data = self.assert_created_course(number_suffix=uuid4().hex)

        # unseed the forums for the first course
        course_id = _get_course_id(test_course_data)
        delete_course_and_groups(course_id, commit=True)
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

        delete_course_and_groups(course_id, commit=True)
        # check that user's enrollment for this course is not deleted
        self.assertTrue(CourseEnrollment.is_enrolled(self.user, course_id))
        # check that user has form role "Student" for this course even after deleting it
        self.assertTrue(self.user.roles.filter(name="Student", course_id=course_id))  # pylint: disable=no-member

    def test_create_course_duplicate_course(self):
        """Test new course creation - error path"""
        self.client.ajax_post('/course', self.course_data)
        self.assert_course_creation_failed('There is already a course defined with the same organization, course number, and course run. Please change either organization or course number to be unique.')

    def assert_course_creation_failed(self, error_message):
        """
        Checks that the course did not get created
        """
        course_id = _get_course_id(self.course_data)
        initially_enrolled = CourseEnrollment.is_enrolled(self.user, course_id)
        resp = self.client.ajax_post('/course', self.course_data)
        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertEqual(data['ErrMsg'], error_message)
        # One test case involves trying to create the same course twice. Hence for that course,
        # the user will be enrolled. In the other cases, initially_enrolled will be False.
        self.assertEqual(initially_enrolled, CourseEnrollment.is_enrolled(self.user, course_id))

    def test_create_course_duplicate_number(self):
        """Test new course creation - error path"""
        self.client.ajax_post('/course', self.course_data)
        self.course_data['display_name'] = 'Robot Super Course Two'
        self.course_data['run'] = '2013_Summer'

        self.assert_course_creation_failed('There is already a course defined with the same organization and course number. Please change at least one field to be unique.')

    def test_create_course_case_change(self):
        """Test new course creation - error path due to case insensitive name equality"""
        self.course_data['number'] = 'capital'
        self.client.ajax_post('/course', self.course_data)
        cache_current = self.course_data['org']
        self.course_data['org'] = self.course_data['org'].lower()
        self.assert_course_creation_failed('There is already a course defined with the same organization and course number. Please change at least one field to be unique.')
        self.course_data['org'] = cache_current

        self.client.ajax_post('/course', self.course_data)
        cache_current = self.course_data['number']
        self.course_data['number'] = self.course_data['number'].upper()
        self.assert_course_creation_failed('There is already a course defined with the same organization and course number. Please change at least one field to be unique.')

    def test_course_substring(self):
        """
        Test that a new course can be created whose name is a substring of an existing course
        """
        self.client.ajax_post('/course', self.course_data)
        cache_current = self.course_data['number']
        self.course_data['number'] = '{}a'.format(self.course_data['number'])
        resp = self.client.ajax_post('/course', self.course_data)
        self.assertEqual(resp.status_code, 200)
        self.course_data['number'] = cache_current
        self.course_data['org'] = 'a{}'.format(self.course_data['org'])
        resp = self.client.ajax_post('/course', self.course_data)
        self.assertEqual(resp.status_code, 200)

    def test_create_course_with_bad_organization(self):
        """Test new course creation - error path for bad organization name"""
        self.course_data['org'] = 'University of California, Berkeley'
        self.assert_course_creation_failed(
            "Unable to create course 'Robot Super Course'.\n\nInvalid characters in u'University of California, Berkeley'.")

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

    def assert_course_permission_denied(self):
        """
        Checks that the course did not get created due to a PermissionError.
        """
        resp = self.client.ajax_post('/course', self.course_data)
        self.assertEqual(resp.status_code, 403)

    def test_course_index_view_with_no_courses(self):
        """Test viewing the index page with no courses"""
        # Create a course so there is something to view
        resp = self.client.get_html('/course')
        self.assertContains(
            resp,
            '<h1 class="page-header">My Courses</h1>',
            status_code=200,
            html=True
        )
        _test_no_locations(self, resp)

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
        resp = self.client.get_html('/course')
        self.assertContains(
            resp,
            '<h3 class="course-title">Robot Super Educational Course</h3>',
            status_code=200,
            html=True
        )
        _test_no_locations(self, resp)

    def test_course_overview_view_with_course(self):
        """Test viewing the course overview page with an existing course"""
        CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')

        loc = Location(['i4x', 'MITx', '999', 'course', Location.clean('Robot Super Course'), None])
        resp = self._show_course_overview(loc)
        self.assertContains(
            resp,
            '<article class="courseware-overview" data-locator="MITx.999.Robot_Super_Course/branch/draft/block/Robot_Super_Course">',
            status_code=200,
            html=True
        )

    def test_create_item(self):
        """Test creating a new xblock instance."""
        locator = _course_factory_create_course()

        section_data = {
            'parent_locator': unicode(locator),
            'category': 'chapter',
            'display_name': 'Section One',
        }

        resp = self.client.ajax_post('/xblock', section_data)
        _test_no_locations(self, resp, html=False)

        self.assertEqual(resp.status_code, 200)
        data = parse_json(resp)
        self.assertRegexpMatches(
            data['locator'],
            r"^MITx.999.Robot_Super_Course/branch/draft/block/chapter([0-9]|[a-f]){3,}$"
        )

    def test_capa_module(self):
        """Test that a problem treats markdown specially."""
        locator = _course_factory_create_course()

        problem_data = {
            'parent_locator': unicode(locator),
            'category': 'problem'
        }

        resp = self.client.ajax_post('/xblock', problem_data)

        self.assertEqual(resp.status_code, 200)
        payload = parse_json(resp)
        problem_loc = loc_mapper().translate_locator_to_location(BlockUsageLocator(payload['locator']))
        problem = get_modulestore(problem_loc).get_item(problem_loc)
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
        def test_get_html(page):
            # Helper function for getting HTML for a page in Studio and
            # checking that it does not error.
            resp = self.client.get_html(new_location.url_reverse(page))
            self.assertEqual(resp.status_code, 200)
            _test_no_locations(self, resp)

        import_from_xml(modulestore('direct'), 'common/test/data/', ['simple'])
        loc = Location(['i4x', 'edX', 'simple', 'course', '2012_Fall', None])
        new_location = loc_mapper().translate_location(loc, True, True)

        resp = self._show_course_overview(loc)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Chapter 2')

        # go to various pages
        test_get_html('import')
        test_get_html('export')
        test_get_html('course_team')
        test_get_html('course_info')
        test_get_html('checklists')
        test_get_html('assets')
        test_get_html('tabs')
        test_get_html('settings/details')
        test_get_html('settings/grading')
        test_get_html('settings/advanced')
        test_get_html('textbooks')

        # go look at a subsection page
        subsection_location = loc.replace(category='sequential', name='test_sequence')
        subsection_locator = loc_mapper().translate_location(subsection_location, True, True)
        resp = self.client.get_html(subsection_locator.url_reverse('subsection'))
        self.assertEqual(resp.status_code, 200)
        _test_no_locations(self, resp)

        # go look at the Edit page
        unit_location = loc.replace(category='vertical', name='test_vertical')
        unit_locator = loc_mapper().translate_location(unit_location, True, True)
        resp = self.client.get_html(unit_locator.url_reverse('unit'))
        self.assertEqual(resp.status_code, 200)
        _test_no_locations(self, resp)

        def delete_item(category, name):
            """ Helper method for testing the deletion of an xblock item. """
            del_loc = loc.replace(category=category, name=name)
            del_location = loc_mapper().translate_location(del_loc, True, True)
            resp = self.client.delete(del_location.url_reverse('xblock'))
            self.assertEqual(resp.status_code, 204)
            _test_no_locations(self, resp, status_code=204, html=False)

        # delete a component
        delete_item(category='html', name='test_html')

        # delete a unit
        delete_item(category='vertical', name='test_vertical')

        # delete a unit
        delete_item(category='sequential', name='test_sequence')

        # delete a chapter
        delete_item(category='chapter', name='chapter_2')

    def test_import_into_new_course_id(self):
        module_store = modulestore('direct')
        target_course_id = _get_course_id(self.course_data)
        _create_course(self, target_course_id, self.course_data)

        import_from_xml(module_store, 'common/test/data/', ['toy'], target_course_id=target_course_id)

        modules = module_store.get_items(target_course_id)

        # we should have a number of modules in there
        # we can't specify an exact number since it'll always be changing
        self.assertGreater(len(modules), 10)

        #
        # test various re-namespacing elements
        #

        # first check PDF textbooks, to make sure the url paths got updated
        course_module = module_store.get_course(target_course_id)

        self.assertEquals(len(course_module.pdf_textbooks), 1)
        self.assertEquals(len(course_module.pdf_textbooks[0]["chapters"]), 2)
        self.assertEquals(course_module.pdf_textbooks[0]["chapters"][0]["url"], '/c4x/MITx/999/asset/Chapter1.pdf')
        self.assertEquals(course_module.pdf_textbooks[0]["chapters"][1]["url"], '/c4x/MITx/999/asset/Chapter2.pdf')

    def test_import_into_new_course_id_wiki_slug_renamespacing(self):
        module_store = modulestore('direct')

        target_course_key = _get_course_id(self.course_data)
        _create_course(self, target_course_key, self.course_data)

        # Import a course with wiki_slug == location.course
        import_from_xml(module_store, 'common/test/data/', ['toy'], target_course_id=target_course_key)
        course_module = module_store.get_course(target_course_key)
        self.assertEquals(course_module.wiki_slug, 'MITx.999.2013_Spring')

        # Now try importing a course with wiki_slug == '{0}{1}{2}'.format(location.org, location.course, location.name)
        import_from_xml(module_store, 'common/test/data/', ['two_toys'], target_course_id=target_course_key)
        course_module = module_store.get_course(target_course_key)
        self.assertEquals(course_module.wiki_slug, 'MITx.999.2013_Spring')

    def test_import_metadata_with_attempts_empty_string(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['simple'])
        did_load_item = False
        try:
            module_store.get_item(Location(['i4x', 'edX', 'simple', 'problem', 'ps01-simple', None]))
            did_load_item = True
        except ItemNotFoundError:
            pass

        # make sure we found the item (e.g. it didn't error while loading)
        self.assertTrue(did_load_item)

    def test_forum_id_generation(self):
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')

        new_component_location = Location('i4x', 'edX', '999', 'discussion', 'new_component')

        # crate a new module and add it as a child to a vertical
        module_store.create_and_save_xmodule(new_component_location)

        new_discussion_item = module_store.get_item(new_component_location)

        self.assertNotEquals(new_discussion_item.discussion_id, '$$GUID$$')

    def test_update_modulestore_signal_did_fire(self):
        module_store = modulestore('direct')
        CourseFactory.create(org='edX', course='999', display_name='Robot Super Course')

        try:
            module_store.modulestore_update_signal = Signal(providing_args=['modulestore', 'course_id', 'location'])

            self.got_signal = False

            def _signal_hander(modulestore=None, course_id=None, location=None, **kwargs):
                self.got_signal = True

            module_store.modulestore_update_signal.connect(_signal_hander)

            new_component_location = Location('i4x', 'edX', '999', 'html', 'new_component')

            # crate a new module
            module_store.create_and_save_xmodule(new_component_location)

        finally:
            module_store.modulestore_update_signal = None

        self.assertTrue(self.got_signal)

    def test_metadata_inheritance(self):
        module_store = modulestore('direct')
        import_from_xml(module_store, 'common/test/data/', ['toy'])

        course = module_store.get_item(Location(['i4x', 'edX', 'toy', 'course', '2012_Fall', None]))

        verticals = module_store.get_items(Location('i4x', 'edX', 'toy', 'vertical', None, None))

        # let's assert on the metadata_inheritance on an existing vertical
        for vertical in verticals:
            self.assertEqual(course.xqa_key, vertical.xqa_key)
            self.assertEqual(course.start, vertical.start)

        self.assertGreater(len(verticals), 0)

        new_component_location = Location('i4x', 'edX', 'toy', 'html', 'new_component')

        # crate a new module and add it as a child to a vertical
        module_store.create_and_save_xmodule(new_component_location)
        parent = verticals[0]
        parent.children.append(new_component_location.url())
        module_store.update_item(parent, self.user.id)

        # flush the cache
        module_store.refresh_cached_metadata_inheritance_tree(new_component_location)
        new_module = module_store.get_item(new_component_location)

        # check for grace period definition which should be defined at the course level
        self.assertEqual(parent.graceperiod, new_module.graceperiod)
        self.assertEqual(parent.start, new_module.start)
        self.assertEqual(course.start, new_module.start)

        self.assertEqual(course.xqa_key, new_module.xqa_key)

        #
        # now let's define an override at the leaf node level
        #
        new_module.graceperiod = timedelta(1)
        module_store.update_item(new_module, self.user.id)

        # flush the cache and refetch
        module_store.refresh_cached_metadata_inheritance_tree(new_component_location)
        new_module = module_store.get_item(new_component_location)

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
        module_store = modulestore('direct')
        fetched_course = module_store.get_item(course.location)
        fetched_item = module_store.get_item(vertical.location)
        self.assertIsNotNone(fetched_course.start)
        self.assertEqual(course.start, fetched_course.start)
        self.assertEqual(fetched_course.start, fetched_item.start)
        self.assertEqual(course.textbooks, fetched_course.textbooks)
        # is this test too strict? i.e., it requires the dicts to be ==
        self.assertEqual(course.checklists, fetched_course.checklists)

    def test_image_import(self):
        """Test backwards compatibilty of course image."""
        module_store = modulestore('direct')

        content_store = contentstore()

        # Use conditional_and_poll, as it's got an image already
        import_from_xml(
            module_store,
            'common/test/data/',
            ['conditional_and_poll'],
            static_content_store=content_store
        )

        course = module_store.get_courses()[0]

        # Make sure the course image is set to the right place
        self.assertEqual(course.course_image, 'images_course_image.jpg')

        # Ensure that the imported course image is present -- this shouldn't raise an exception
        location = course.location._replace(tag='c4x', category='asset', name=course.course_image)
        content_store.find(location)

    def _show_course_overview(self, location):
        """
        Show the course overview page.
        """
        new_location = loc_mapper().translate_location(location, True, True)
        resp = self.client.get_html(new_location.url_reverse('course/', ''))
        _test_no_locations(self, resp)
        return resp

    def test_wiki_slug(self):
        """When creating a course a unique wiki_slug should be set."""

        course_key = _get_course_id(self.course_data)
        _create_course(self, course_key, self.course_data)
        course_module = modulestore('direct').get_course(course_key)
        self.assertEquals(course_module.wiki_slug, 'MITx.999.2013_Spring')


@override_settings(MODULESTORE=TEST_MODULESTORE)
class MetadataSaveTestCase(ModuleStoreTestCase):
    """Test that metadata is correctly cached and decached."""

    def setUp(self):
        CourseFactory.create(
            org='edX', course='999', display_name='Robot Super Course')
        course_location = Location(
            ['i4x', 'edX', '999', 'course', 'Robot_Super_Course', None])

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
            parent_location=course_location, category='video',
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
        get_modulestore(location).update_item(self.video_descriptor, '**replace_user**')
        module = get_modulestore(location).get_item(location)

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
        _test_no_locations(self, resp, status_code)

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
    new_location = loc_mapper().translate_location(
        CourseKey.make_usage_key(course_key, 'course', course_key.run), False, True
    )

    response = test.client.ajax_post('/course', course_data)
    test.assertEqual(response.status_code, 200)
    data = parse_json(response)
    test.assertNotIn('ErrMsg', data)
    test.assertEqual(data['url'], new_location.url_reverse("course"))


def _course_factory_create_course():
    """
    Creates a course via the CourseFactory and returns the locator for it.
    """
    course = CourseFactory.create(org='MITx', course='999', display_name='Robot Super Course')
    return loc_mapper().translate_location(course.location, False, True)


def _get_course_id(course_data):
    """Returns the course ID (org/number/run)."""
    return SlashSeparatedCourseKey(course_data['org'], course_data['number'], course_data['run'])


def _test_no_locations(test, resp, status_code=200, html=True):
    """
    Verifies that "i4x", which appears in old locations, but not
    new locators, does not appear in the HTML response output.
    Used to verify that database refactoring is complete.
    """
    test.assertNotContains(resp, 'i4x', status_code=status_code, html=html)
    if html:
        # For HTML pages, it is nice to call the method with html=True because
        # it checks that the HTML properly parses. However, it won't find i4x usages
        # in JavaScript blocks.
        content = resp.content
        hits = len(re.findall(r"(?<!jump_to/)i4x://", content))
        test.assertEqual(hits, 0, "i4x found outside of LMS jump-to links")
