"""
Tests for contentstore.views.preview.py
"""
from django.test import TestCase
from django.test.client import RequestFactory

from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory

from contentstore.views.preview import get_preview_fragment


class GetPreviewHtmlTestCase(TestCase):
    """
    Tests for get_preview_fragment.

    Note that there are other existing test cases in test_contentstore that indirectly execute
    get_preview_fragment via the xblock RESTful API.
    """

    def test_preview_fragment(self):
        """
        Test for calling get_preview_html.

        This test used to be specifically about Locators (ensuring that they did not
        get translated to Locations). The test now has questionable value.
        """
        course = CourseFactory.create()
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        html = get_preview_fragment(request, html, {}).content

        # Verify student view html is returned, and the usage ID is as expected.
        self.assertRegexpMatches(
            html,
            'data-usage-id="i4x://MITx/999/html/html_[0-9]*"'
        )
        self.assertRegexpMatches(html, '<html>foobar</html>')
