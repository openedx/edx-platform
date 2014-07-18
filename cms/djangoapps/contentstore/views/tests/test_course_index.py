"""
Unit tests for getting the list of courses and the course outline.
"""
import json
import lxml

from contentstore.tests.utils import CourseTestCase
from contentstore.utils import reverse_course_url
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from opaque_keys.edx.locator import Locator
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
        self.assertTrue(json_response['is_container'])
        self.assertFalse(json_response['is_draft'])

        # Now verify the first child
        children = json_response['children']
        self.assertTrue(len(children) > 0)
        first_child_response = children[0]
        self.assertEqual(first_child_response['category'], 'chapter')
        self.assertEqual(first_child_response['id'], 'i4x://MITx/999/chapter/Week_1')
        self.assertEqual(first_child_response['display_name'], 'Week 1')
        self.assertTrue(first_child_response['is_container'])
        self.assertFalse(first_child_response['is_draft'])
        self.assertTrue(len(first_child_response['children']) > 0)

        # Finally, validate the entire response for consistency
        self.assert_correct_json_response(json_response)

    def assert_correct_json_response(self, json_response):
        """
        Asserts that the JSON response is syntactically consistent
        """
        self.assertIsNotNone(json_response['display_name'])
        self.assertIsNotNone(json_response['id'])
        self.assertIsNotNone(json_response['category'])
        self.assertIsNotNone(json_response['is_draft'])
        self.assertIsNotNone(json_response['is_container'])
        if json_response['is_container']:
            for child_response in json_response['children']:
                self.assert_correct_json_response(child_response)
        else:
            self.assertFalse('children' in json_response)
