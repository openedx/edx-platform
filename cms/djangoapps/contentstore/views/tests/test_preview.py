"""
Tests for contentstore.views.preview.py
"""
import ddt
from mock import Mock
from xblock.core import XBlock

from django.test import TestCase
from django.test.client import RequestFactory

from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from contentstore.views.preview import get_preview_fragment, _preview_module_system


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
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        # Verify student view html is returned, and the usage ID is as expected.
        html_pattern = unicode(course.id.make_usage_key('html', 'html_')).replace('html_', r'html_[0-9]*')
        self.assertRegexpMatches(
            html,
            'data-usage-id="{}"'.format(html_pattern)
        )
        self.assertRegexpMatches(html, '<html>foobar</html>')


@XBlock.needs("i18n")
@XBlock.needs("user")
@XBlock.needs("course")
class PureXBlock(XBlock):
    """
    Pure XBlock to use in tests.
    """
    pass


@ddt.ddt
class StudioXBlockServiceBindingTest(ModuleStoreTestCase):
    """
    Tests that the Studio Module System (XBlock Runtime) provides an expected set of services.
    """
    def setUp(self):
        """
        Set up the user and request that will be used.
        """
        super(StudioXBlockServiceBindingTest, self).setUp()
        self.user = UserFactory()
        self.course = CourseFactory.create()
        self.request = Mock()

    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    @ddt.data("course", "user", "i18n")
    def test_expected_services_exist(self, expected_service):
        """
        Tests that the 'course', 'user' and 'i18n' services are provided by the Studio runtime.
        """
        descriptor = ItemFactory(category="pure", parent=self.course)
        runtime = _preview_module_system(
            self.request,
            descriptor,
        )
        service = runtime.service(descriptor, expected_service)
        self.assertIsNotNone(service)
