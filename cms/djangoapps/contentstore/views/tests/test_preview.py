"""
Tests for contentstore.views.preview.py
"""
from django.test import TestCase
from django.test.client import RequestFactory

from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import loc_mapper

from contentstore.views.preview import get_preview_fragment


class GetPreviewHtmlTestCase(TestCase):
    """
    Tests for get_preview_html.

    Note that there are other existing test cases in test_contentstore that indirectly execute
    get_preview_html via the xblock RESTful API.
    """

    def test_preview_handler_locator(self):
        """
        Test for calling get_preview_html when descriptor.location is a Locator.
        """
        course = CourseFactory.create()
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        locator = loc_mapper().translate_location(
            course.location.course_id, html.location, True, True
        )

        # Change the stored location to a locator.
        html.location = locator
        html.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Must call get_preview_fragment directly, as going through xblock RESTful API will attempt
        # to use item.location as a Location.
        html = get_preview_fragment(request, html, {}).content
        # Verify student view html is returned, and there are no old locations in it.
        self.assertRegexpMatches(
            html,
            'data-usage-id="MITx.999.Robot_Super_Course;_branch;_published;_block;_html_[0-9]*"'
        )
        self.assertRegexpMatches(html, '<html>foobar</html>')
        self.assertNotRegexpMatches(html, 'i4x')
