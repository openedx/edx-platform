"""
Unit tests for getting the list of courses and the course outline.
"""
import ddt
import json
import lxml
import datetime
import mock
import pytz

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext as _

from contentstore.courseware_index import CoursewareSearchIndexer, SearchIndexingError
from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url, reverse_library_url, add_instructor, reverse_usage_url
from contentstore.views.course import (
    course_outline_initial_state, reindex_course_and_check_access, _deprecated_blocks_info
)
from contentstore.views.item import create_xblock_info, VisibilityState
from course_action_state.managers import CourseRerunUIStateManager
from course_action_state.models import CourseRerunState
from opaque_keys.edx.locator import CourseLocator
from search.api import perform_search
from student.auth import has_course_author_access
from student.tests.factories import UserFactory
from util.date_utils import get_default_time_display
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.exceptions import ItemNotFoundError
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory, LibraryFactory


class TestCourseIndex(CourseTestCase):
    """
    Unit tests for getting the list of courses and the course outline.
    """
    def setUp(self):
        """
        Add a course with odd characters in the fields
        """
        super(TestCourseIndex, self).setUp()
        # had a problem where index showed course but has_access failed to retrieve it for non-staff
        self.odd_course = CourseFactory.create(
            org='test.org_1-2',
            number='test-2.3_course',
            display_name='dotted.course.name-2',
        )

    def check_index_and_outline(self, authed_client):
        """
        Test getting the list of courses and then pulling up their outlines
        """
        index_url = '/home/'
        index_response = authed_client.get(index_url, {}, HTTP_ACCEPT='text/html')
        parsed_html = lxml.html.fromstring(index_response.content)
        course_link_eles = parsed_html.find_class('course-link')
        self.assertGreaterEqual(len(course_link_eles), 2)
        for link in course_link_eles:
            self.assertRegexpMatches(
                link.get("href"),
                'course/{}'.format(settings.COURSE_KEY_PATTERN)
            )
            # now test that url
            outline_response = authed_client.get(link.get("href"), {}, HTTP_ACCEPT='text/html')
            # ensure it has the expected 2 self referential links
            outline_parsed = lxml.html.fromstring(outline_response.content)
            outline_link = outline_parsed.find_class('course-link')[0]
            self.assertEqual(outline_link.get("href"), link.get("href"))
            course_menu_link = outline_parsed.find_class('nav-course-courseware-outline')[0]
            self.assertEqual(course_menu_link.find("a").get("href"), link.get("href"))

    def test_libraries_on_course_index(self):
        """
        Test getting the list of libraries from the course listing page
        """
        # Add a library:
        lib1 = LibraryFactory.create()

        index_url = '/home/'
        index_response = self.client.get(index_url, {}, HTTP_ACCEPT='text/html')
        parsed_html = lxml.html.fromstring(index_response.content)
        library_link_elements = parsed_html.find_class('library-link')
        self.assertEqual(len(library_link_elements), 1)
        link = library_link_elements[0]
        self.assertEqual(
            link.get("href"),
            reverse_library_url('library_handler', lib1.location.library_key),
        )
        # now test that url
        outline_response = self.client.get(link.get("href"), {}, HTTP_ACCEPT='text/html')
        self.assertEqual(outline_response.status_code, 200)

    def test_is_staff_access(self):
        """
        Test that people with is_staff see the courses and can navigate into them
        """
        self.check_index_and_outline(self.client)

    def test_negative_conditions(self):
        """
        Test the error conditions for the access
        """
        outline_url = reverse_course_url('course_handler', self.course.id)
        # register a non-staff member and try to delete the course branch
        non_staff_client, _ = self.create_non_staff_authed_user_client()
        response = non_staff_client.delete(outline_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)

    def test_course_staff_access(self):
        """
        Make and register course_staff and ensure they can access the courses
        """
        course_staff_client, course_staff = self.create_non_staff_authed_user_client()
        for course in [self.course, self.odd_course]:
            permission_url = reverse_course_url('course_team_handler', course.id, kwargs={'email': course_staff.email})

            self.client.post(
                permission_url,
                data=json.dumps({"role": "staff"}),
                content_type="application/json",
                HTTP_ACCEPT="application/json",
            )

        # test access
        self.check_index_and_outline(course_staff_client)

    def test_json_responses(self):
        outline_url = reverse_course_url('course_handler', self.course.id)
        chapter = ItemFactory.create(parent_location=self.course.location, category='chapter', display_name="Week 1")
        lesson = ItemFactory.create(parent_location=chapter.location, category='sequential', display_name="Lesson 1")
        subsection = ItemFactory.create(parent_location=lesson.location, category='vertical', display_name='Subsection 1')
        ItemFactory.create(parent_location=subsection.location, category="video", display_name="My Video")

        resp = self.client.get(outline_url, HTTP_ACCEPT='application/json')
        json_response = json.loads(resp.content)

        # First spot check some values in the root response
        self.assertEqual(json_response['category'], 'course')
        self.assertEqual(json_response['id'], unicode(self.course.location))
        self.assertEqual(json_response['display_name'], self.course.display_name)
        self.assertTrue(json_response['published'])
        self.assertIsNone(json_response['visibility_state'])

        # Now verify the first child
        children = json_response['child_info']['children']
        self.assertTrue(len(children) > 0)
        first_child_response = children[0]
        self.assertEqual(first_child_response['category'], 'chapter')
        self.assertEqual(first_child_response['id'], unicode(chapter.location))
        self.assertEqual(first_child_response['display_name'], 'Week 1')
        self.assertTrue(json_response['published'])
        self.assertEqual(first_child_response['visibility_state'], VisibilityState.unscheduled)
        self.assertTrue(len(first_child_response['child_info']['children']) > 0)

        # Finally, validate the entire response for consistency
        self.assert_correct_json_response(json_response)

    def test_notifications_handler_get(self):
        state = CourseRerunUIStateManager.State.FAILED
        action = CourseRerunUIStateManager.ACTION
        should_display = True

        # try when no notification exists
        notification_url = reverse_course_url('course_notifications_handler', self.course.id, kwargs={
            'action_state_id': 1,
        })

        resp = self.client.get(notification_url, HTTP_ACCEPT='application/json')

        # verify that we get an empty dict out
        self.assertEquals(resp.status_code, 400)

        # create a test notification
        rerun_state = CourseRerunState.objects.update_state(course_key=self.course.id, new_state=state, allow_not_found=True)
        CourseRerunState.objects.update_should_display(entry_id=rerun_state.id, user=UserFactory(), should_display=should_display)

        # try to get information on this notification
        notification_url = reverse_course_url('course_notifications_handler', self.course.id, kwargs={
            'action_state_id': rerun_state.id,
        })
        resp = self.client.get(notification_url, HTTP_ACCEPT='application/json')

        json_response = json.loads(resp.content)

        self.assertEquals(json_response['state'], state)
        self.assertEquals(json_response['action'], action)
        self.assertEquals(json_response['should_display'], should_display)

    def test_notifications_handler_dismiss(self):
        state = CourseRerunUIStateManager.State.FAILED
        should_display = True
        rerun_course_key = CourseLocator(org='testx', course='test_course', run='test_run')

        # add an instructor to this course
        user2 = UserFactory()
        add_instructor(rerun_course_key, self.user, user2)

        # create a test notification
        rerun_state = CourseRerunState.objects.update_state(course_key=rerun_course_key, new_state=state, allow_not_found=True)
        CourseRerunState.objects.update_should_display(entry_id=rerun_state.id, user=user2, should_display=should_display)

        # try to get information on this notification
        notification_dismiss_url = reverse_course_url('course_notifications_handler', self.course.id, kwargs={
            'action_state_id': rerun_state.id,
        })
        resp = self.client.delete(notification_dismiss_url)
        self.assertEquals(resp.status_code, 200)

        with self.assertRaises(CourseRerunState.DoesNotExist):
            # delete nofications that are dismissed
            CourseRerunState.objects.get(id=rerun_state.id)

        self.assertFalse(has_course_author_access(user2, rerun_course_key))

    def assert_correct_json_response(self, json_response):
        """
        Asserts that the JSON response is syntactically consistent
        """
        self.assertIsNotNone(json_response['display_name'])
        self.assertIsNotNone(json_response['id'])
        self.assertIsNotNone(json_response['category'])
        self.assertTrue(json_response['published'])
        if json_response.get('child_info', None):
            for child_response in json_response['child_info']['children']:
                self.assert_correct_json_response(child_response)


@ddt.ddt
class TestCourseOutline(CourseTestCase):
    """
    Unit tests for the course outline.
    """
    def setUp(self):
        """
        Set up the for the course outline tests.
        """
        super(TestCourseOutline, self).setUp()

        self.chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Week 1"
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name="Lesson 1"
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 1'
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location, category="video", display_name="My Video"
        )

    def test_json_responses(self):
        """
        Verify the JSON responses returned for the course.
        """
        outline_url = reverse_course_url('course_handler', self.course.id)
        resp = self.client.get(outline_url, HTTP_ACCEPT='application/json')
        json_response = json.loads(resp.content)

        # First spot check some values in the root response
        self.assertEqual(json_response['category'], 'course')
        self.assertEqual(json_response['id'], unicode(self.course.location))
        self.assertEqual(json_response['display_name'], self.course.display_name)
        self.assertTrue(json_response['published'])
        self.assertIsNone(json_response['visibility_state'])

        # Now verify the first child
        children = json_response['child_info']['children']
        self.assertTrue(len(children) > 0)
        first_child_response = children[0]
        self.assertEqual(first_child_response['category'], 'chapter')
        self.assertEqual(first_child_response['id'], unicode(self.chapter.location))
        self.assertEqual(first_child_response['display_name'], 'Week 1')
        self.assertTrue(json_response['published'])
        self.assertEqual(first_child_response['visibility_state'], VisibilityState.unscheduled)
        self.assertTrue(len(first_child_response['child_info']['children']) > 0)

        # Finally, validate the entire response for consistency
        self.assert_correct_json_response(json_response)

    def assert_correct_json_response(self, json_response):
        """
        Asserts that the JSON response is syntactically consistent
        """
        self.assertIsNotNone(json_response['display_name'])
        self.assertIsNotNone(json_response['id'])
        self.assertIsNotNone(json_response['category'])
        self.assertTrue(json_response['published'])
        if json_response.get('child_info', None):
            for child_response in json_response['child_info']['children']:
                self.assert_correct_json_response(child_response)

    def test_course_outline_initial_state(self):
        course_module = modulestore().get_item(self.course.location)
        course_structure = create_xblock_info(
            course_module,
            include_child_info=True,
            include_children_predicate=lambda xblock: not xblock.category == 'vertical'
        )

        # Verify that None is returned for a non-existent locator
        self.assertIsNone(course_outline_initial_state('no-such-locator', course_structure))

        # Verify that the correct initial state is returned for the test chapter
        chapter_locator = unicode(self.chapter.location)
        initial_state = course_outline_initial_state(chapter_locator, course_structure)
        self.assertEqual(initial_state['locator_to_show'], chapter_locator)
        expanded_locators = initial_state['expanded_locators']
        self.assertIn(unicode(self.sequential.location), expanded_locators)
        self.assertIn(unicode(self.vertical.location), expanded_locators)

    def test_start_date_on_page(self):
        """
        Verify that the course start date is included on the course outline page.
        """
        def _get_release_date(response):
            """Return the release date from the course page"""
            parsed_html = lxml.html.fromstring(response.content)
            return parsed_html.find_class('course-status')[0].find_class('status-release-value')[0].text_content()

        def _assert_settings_link_present(response):
            """
            Asserts there's a course settings link on the course page by the course release date.
            """
            parsed_html = lxml.html.fromstring(response.content)
            settings_link = parsed_html.find_class('course-status')[0].find_class('action-edit')[0].find('a')
            self.assertIsNotNone(settings_link)
            self.assertEqual(settings_link.get('href'), reverse_course_url('settings_handler', self.course.id))

        outline_url = reverse_course_url('course_handler', self.course.id)
        response = self.client.get(outline_url, {}, HTTP_ACCEPT='text/html')

        # A course with the default release date should display as "Unscheduled"
        self.assertEqual(_get_release_date(response), 'Unscheduled')
        _assert_settings_link_present(response)

        self.course.start = datetime.datetime(2014, 1, 1, tzinfo=pytz.utc)
        modulestore().update_item(self.course, ModuleStoreEnum.UserID.test)
        response = self.client.get(outline_url, {}, HTTP_ACCEPT='text/html')

        self.assertEqual(_get_release_date(response), get_default_time_display(self.course.start))
        _assert_settings_link_present(response)

    def _create_test_data(self, course_module, create_blocks=False, publish=True, block_types=None):
        """
        Create data for test.
        """
        if create_blocks:
            for block_type in block_types:
                ItemFactory.create(
                    parent_location=self.vertical.location,
                    category=block_type,
                    display_name='{} Problem'.format(block_type)
                )

            if not publish:
                self.store.unpublish(self.vertical.location, self.user.id)

        course_module.advanced_modules.extend(block_types)

    def _verify_deprecated_info(self, course_id, advanced_modules, info, deprecated_block_types):
        """
        Verify deprecated info.
        """
        expected_blocks = []
        for block_type in deprecated_block_types:
            expected_blocks.append(
                [
                    reverse_usage_url('container_handler', self.vertical.location),
                    '{} Problem'.format(block_type)
                ]
            )

        self.assertEqual(info['block_types'], deprecated_block_types)
        self.assertEqual(
            info['block_types_enabled'],
            any(component in advanced_modules for component in deprecated_block_types)
        )
        self.assertItemsEqual(info['blocks'], expected_blocks)
        self.assertEqual(
            info['advance_settings_url'],
            reverse_course_url('advanced_settings_handler', course_id)
        )

    @ddt.data(
        {'publish': True},
        {'publish': False},
    )
    @ddt.unpack
    def test_verify_deprecated_warning_message_with_single_feature(self, publish):
        """
        Verify deprecated warning info for single deprecated feature.
        """
        block_types = settings.DEPRECATED_BLOCK_TYPES
        course_module = modulestore().get_item(self.course.location)
        self._create_test_data(course_module, create_blocks=True, block_types=block_types, publish=publish)
        info = _deprecated_blocks_info(course_module, block_types)
        self._verify_deprecated_info(
            course_module.id,
            course_module.advanced_modules,
            info,
            block_types
        )

    def test_verify_deprecated_warning_message_with_multiple_features(self):
        """
        Verify deprecated warning info for multiple deprecated features.
        """
        block_types = ['peergrading', 'combinedopenended', 'openassessment']
        course_module = modulestore().get_item(self.course.location)
        self._create_test_data(course_module, create_blocks=True, block_types=block_types)

        info = _deprecated_blocks_info(course_module, block_types)
        self._verify_deprecated_info(course_module.id, course_module.advanced_modules, info, block_types)

    @ddt.data(
        {'delete_vertical': True},
        {'delete_vertical': False},
    )
    @ddt.unpack
    def test_deprecated_blocks_list_updated_correctly(self, delete_vertical):
        """
        Verify that deprecated blocks list shown on banner is updated correctly.

        Here is the scenario:
            This list of deprecated blocks shown on banner contains published
            and un-published blocks. That list should be updated when we delete
            un-published block(s). This behavior should be same if we delete
            unpublished vertical or problem.
        """
        block_types = ['peergrading']
        course_module = modulestore().get_item(self.course.location)

        vertical1 = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Vert1 Subsection1'
        )
        problem1 = ItemFactory.create(
            parent_location=vertical1.location,
            category='peergrading',
            display_name='peergrading problem in vert1',
            publish_item=False
        )

        info = _deprecated_blocks_info(course_module, block_types)
        # info['blocks'] should be empty here because there is nothing
        # published or un-published present
        self.assertEqual(info['blocks'], [])

        vertical2 = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Vert2 Subsection1'
        )
        ItemFactory.create(
            parent_location=vertical2.location,
            category='peergrading',
            display_name='peergrading problem in vert2',
            pubish_item=True
        )
        # At this point CourseStructure will contain both the above
        # published and un-published verticals

        info = _deprecated_blocks_info(course_module, block_types)
        self.assertItemsEqual(
            info['blocks'],
            [
                [reverse_usage_url('container_handler', vertical1.location), 'peergrading problem in vert1'],
                [reverse_usage_url('container_handler', vertical2.location), 'peergrading problem in vert2']
            ]
        )

        # Delete the un-published vertical or problem so that CourseStructure updates its data
        if delete_vertical:
            self.store.delete_item(vertical1.location, self.user.id)
        else:
            self.store.delete_item(problem1.location, self.user.id)

        info = _deprecated_blocks_info(course_module, block_types)
        # info['blocks'] should only contain the info about vertical2 which is published.
        # There shouldn't be any info present about un-published vertical1
        self.assertEqual(
            info['blocks'],
            [[reverse_usage_url('container_handler', vertical2.location), 'peergrading problem in vert2']]
        )


class TestCourseReIndex(CourseTestCase):
    """
    Unit tests for the course outline.
    """

    SUCCESSFUL_RESPONSE = _("Course has been successfully reindexed.")

    def setUp(self):
        """
        Set up the for the course outline tests.
        """

        super(TestCourseReIndex, self).setUp()

        self.course.start = datetime.datetime(2014, 1, 1, tzinfo=pytz.utc)
        modulestore().update_item(self.course, self.user.id)

        self.chapter = ItemFactory.create(
            parent_location=self.course.location, category='chapter', display_name="Week 1"
        )
        self.sequential = ItemFactory.create(
            parent_location=self.chapter.location, category='sequential', display_name="Lesson 1"
        )
        self.vertical = ItemFactory.create(
            parent_location=self.sequential.location, category='vertical', display_name='Subsection 1'
        )
        self.video = ItemFactory.create(
            parent_location=self.vertical.location, category="video", display_name="My Video"
        )

        self.html = ItemFactory.create(
            parent_location=self.vertical.location, category="html", display_name="My HTML",
            data="<div>This is my unique HTML content</div>",

        )

    def test_reindex_course(self):
        """
        Verify that course gets reindexed.
        """
        index_url = reverse_course_url('course_search_index_handler', self.course.id)
        response = self.client.get(index_url, {}, HTTP_ACCEPT='application/json')

        # A course with the default release date should display as "Unscheduled"
        self.assertIn(self.SUCCESSFUL_RESPONSE, response.content)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(index_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.content, '')
        self.assertEqual(response.status_code, 405)

        self.client.logout()
        response = self.client.get(index_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 302)

    def test_negative_conditions(self):
        """
        Test the error conditions for the access
        """
        index_url = reverse_course_url('course_search_index_handler', self.course.id)
        # register a non-staff member and try to delete the course branch
        non_staff_client, _ = self.create_non_staff_authed_user_client()
        response = non_staff_client.get(index_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)

    def test_content_type_none(self):
        """
        Test json content type is set if none is selected
        """
        index_url = reverse_course_url('course_search_index_handler', self.course.id)
        response = self.client.get(index_url, {}, CONTENT_TYPE=None)

        # A course with the default release date should display as "Unscheduled"
        self.assertIn(self.SUCCESSFUL_RESPONSE, response.content)
        self.assertEqual(response.status_code, 200)

    @mock.patch('xmodule.html_module.HtmlDescriptor.index_dictionary')
    def test_reindex_course_search_index_error(self, mock_index_dictionary):
        """
        Test json response with mocked error data for html
        """

        # set mocked exception response
        err = SearchIndexingError
        mock_index_dictionary.return_value = err

        index_url = reverse_course_url('course_search_index_handler', self.course.id)

        # Start manual reindex and check error in response
        response = self.client.get(index_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 500)

    def test_reindex_json_responses(self):
        """
        Test json response with real data
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # Start manual reindex
        reindex_course_and_check_access(self.course.id, self.user)

        # Check results remain the same
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

    @mock.patch('xmodule.video_module.VideoDescriptor.index_dictionary')
    def test_reindex_video_error_json_responses(self, mock_index_dictionary):
        """
        Test json response with mocked error data for video
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = SearchIndexingError
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            reindex_course_and_check_access(self.course.id, self.user)

    @mock.patch('xmodule.html_module.HtmlDescriptor.index_dictionary')
    def test_reindex_html_error_json_responses(self, mock_index_dictionary):
        """
        Test json response with mocked error data for html
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = SearchIndexingError
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            reindex_course_and_check_access(self.course.id, self.user)

    @mock.patch('xmodule.seq_module.SequenceDescriptor.index_dictionary')
    def test_reindex_seq_error_json_responses(self, mock_index_dictionary):
        """
        Test json response with mocked error data for sequence
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = Exception
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            reindex_course_and_check_access(self.course.id, self.user)

    @mock.patch('xmodule.modulestore.mongo.base.MongoModuleStore.get_course')
    def test_reindex_no_item(self, mock_get_course):
        """
        Test system logs an error if no item found.
        """
        # set mocked exception response
        err = ItemNotFoundError
        mock_get_course.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            reindex_course_and_check_access(self.course.id, self.user)

    def test_reindex_no_permissions(self):
        # register a non-staff member and try to delete the course branch
        user2 = UserFactory()
        with self.assertRaises(PermissionDenied):
            reindex_course_and_check_access(self.course.id, user2)

    def test_indexing_responses(self):
        """
        Test do_course_reindex response with real data
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # Start manual reindex
        CoursewareSearchIndexer.do_course_reindex(modulestore(), self.course.id)

        # Check results are the same following reindex
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

    @mock.patch('xmodule.video_module.VideoDescriptor.index_dictionary')
    def test_indexing_video_error_responses(self, mock_index_dictionary):
        """
        Test do_course_reindex response with mocked error data for video
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = Exception
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            CoursewareSearchIndexer.do_course_reindex(modulestore(), self.course.id)

    @mock.patch('xmodule.html_module.HtmlDescriptor.index_dictionary')
    def test_indexing_html_error_responses(self, mock_index_dictionary):
        """
        Test do_course_reindex response with mocked error data for html
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = Exception
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            CoursewareSearchIndexer.do_course_reindex(modulestore(), self.course.id)

    @mock.patch('xmodule.seq_module.SequenceDescriptor.index_dictionary')
    def test_indexing_seq_error_responses(self, mock_index_dictionary):
        """
        Test do_course_reindex response with mocked error data for sequence
        """
        # results are indexed because they are published from ItemFactory
        response = perform_search(
            "unique",
            user=self.user,
            size=10,
            from_=0,
            course_id=unicode(self.course.id))
        self.assertEqual(response['total'], 1)

        # set mocked exception response
        err = Exception
        mock_index_dictionary.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            CoursewareSearchIndexer.do_course_reindex(modulestore(), self.course.id)

    @mock.patch('xmodule.modulestore.mongo.base.MongoModuleStore.get_course')
    def test_indexing_no_item(self, mock_get_course):
        """
        Test system logs an error if no item found.
        """
        # set mocked exception response
        err = ItemNotFoundError
        mock_get_course.return_value = err

        # Start manual reindex and check error in response
        with self.assertRaises(SearchIndexingError):
            CoursewareSearchIndexer.do_course_reindex(modulestore(), self.course.id)
