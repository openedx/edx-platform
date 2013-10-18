"""
Unit tests for getting the list of courses and the course outline.
"""
from django.core.urlresolvers import reverse
import lxml

from contentstore.tests.utils import CourseTestCase
from xmodule.modulestore.django import loc_mapper

class TestCourseIndex(CourseTestCase):
    """
    Unit tests for getting the list of courses and the course outline.
    """
    def test_index(self):
        """
        Test getting the list of courses and then pulling up their outlines
        """
        index_url = reverse('contentstore.views.index')
        index_response = self.client.get(index_url, {}, HTTP_ACCEPT='text/html')
        parsed_html = lxml.html.fromstring(index_response.content)
        course_link_eles = parsed_html.find_class('course-link')
        for link in course_link_eles:
            self.assertRegexpMatches(link.get("href"), r'course/\w+\.\w+\.\w+.*/branch/\w+/block/.*')
            # now test that url
            outline_response = self.client.get(link.get("href"), {}, HTTP_ACCEPT='text/html')
            # ensure it has the expected 2 self referential links
            outline_parsed = lxml.html.fromstring(outline_response.content)
            outline_link = outline_parsed.find_class('course-link')[0]
            self.assertEqual(outline_link.get("href"), link.get("href"))
            course_menu_link = outline_parsed.find_class('nav-course-courseware-outline')[0]
            self.assertEqual(course_menu_link.find("a").get("href"), link.get("href"))

    def test_negative_conditions(self):
        """
        Test the error conditions for the access
        """
        locator = loc_mapper().translate_location(self.course.location.course_id, self.course.location, False, True)
        outline_url = locator.url_reverse('course/', '')
        # register a non-staff member and try to delete the course branch
        non_staff_client = self.createNonStaffAuthedUserClient()
        response = non_staff_client.delete(outline_url, {}, HTTP_ACCEPT='application/json')
        self.assertEqual(response.status_code, 403)
