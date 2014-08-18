"""
Unit tests for getting the list of courses and the course outline.
"""
import json
import lxml
import datetime

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url, add_instructor
from contentstore.views.access import has_course_access
from contentstore.views.course import course_outline_initial_state
from contentstore.views.item import create_xblock_info, VisibilityState
from course_action_state.models import CourseRerunState
from util.date_utils import get_default_time_display
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from opaque_keys.edx.locator import CourseLocator
from student.tests.factories import UserFactory
from course_action_state.managers import CourseRerunUIStateManager
from django.conf import settings


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
        index_url = '/course/'
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
        self.assertEqual(json_response['id'], 'i4x://MITx/999/course/Robot_Super_Course')
        self.assertEqual(json_response['display_name'], 'Robot Super Course')
        self.assertTrue(json_response['published'])
        self.assertIsNone(json_response['visibility_state'])

        # Now verify the first child
        children = json_response['child_info']['children']
        self.assertTrue(len(children) > 0)
        first_child_response = children[0]
        self.assertEqual(first_child_response['category'], 'chapter')
        self.assertEqual(first_child_response['id'], 'i4x://MITx/999/chapter/Week_1')
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

        self.assertFalse(has_course_access(user2, rerun_course_key))

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
        self.assertEqual(json_response['id'], 'i4x://MITx/999/course/Robot_Super_Course')
        self.assertEqual(json_response['display_name'], 'Robot Super Course')
        self.assertTrue(json_response['published'])
        self.assertIsNone(json_response['visibility_state'])

        # Now verify the first child
        children = json_response['child_info']['children']
        self.assertTrue(len(children) > 0)
        first_child_response = children[0]
        self.assertEqual(first_child_response['category'], 'chapter')
        self.assertEqual(first_child_response['id'], 'i4x://MITx/999/chapter/Week_1')
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

        self.course.start = datetime.datetime(2014, 1, 1)
        modulestore().update_item(self.course, ModuleStoreEnum.UserID.test)
        response = self.client.get(outline_url, {}, HTTP_ACCEPT='text/html')

        self.assertEqual(_get_release_date(response), get_default_time_display(self.course.start))
        _assert_settings_link_present(response)
