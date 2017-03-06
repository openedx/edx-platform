"""
Tests for contentstore.views.preview.py
"""
import re
import ddt
from mock import Mock
from xblock.core import XBlock

from django.test.client import RequestFactory

from xblock.core import XBlockAside
from student.tests.factories import UserFactory

from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

from contentstore.views.preview import get_preview_fragment, _preview_module_system
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.tests.test_asides import AsideTestType
from xblock_config.models import StudioConfig
from xmodule.modulestore.django import modulestore


class GetPreviewHtmlTestCase(ModuleStoreTestCase):
    """
    Tests for get_preview_fragment.

    Note that there are other existing test cases in test_contentstore that indirectly execute
    get_preview_fragment via the xblock RESTful API.
    """
    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_fragment(self):
        """
        Test for calling get_preview_html. Ensures data-usage-id is correctly set and
        asides are correctly included.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = True
        config.save()

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
        html_pattern = re.escape(unicode(course.id.make_usage_key('html', 'replaceme'))).replace('replaceme', r'html_[0-9]*')
        self.assertRegexpMatches(
            html,
            'data-usage-id="{}"'.format(html_pattern)
        )
        self.assertRegexpMatches(html, '<html>foobar</html>')
        self.assertRegexpMatches(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertRegexpMatches(html, "Aside rendered")
        # Now ensure the acid_aside is not in the result
        self.assertNotRegexpMatches(html, r"data-block-type=[\"\']acid_aside[\"\']")

        # Ensure about pages don't have asides
        about = modulestore().get_item(course.id.make_usage_key('about', 'overview'))
        html = get_preview_fragment(request, about, context).content
        self.assertNotRegexpMatches(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertNotRegexpMatches(html, "Aside rendered")

    @XBlockAside.register_temp_plugin(AsideTestType, 'test_aside')
    def test_preview_no_asides(self):
        """
        Test for calling get_preview_html. Ensures data-usage-id is correctly set and
        asides are correctly excluded because they are not enabled.
        """
        course = CourseFactory.create(default_store=ModuleStoreEnum.Type.split)
        html = ItemFactory.create(
            parent_location=course.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )

        config = StudioConfig.current()
        config.enabled = False
        config.save()

        request = RequestFactory().get('/dummy-url')
        request.user = UserFactory()
        request.session = {}

        # Call get_preview_fragment directly.
        context = {
            'reorderable_items': set(),
            'read_only': True
        }
        html = get_preview_fragment(request, html, context).content

        self.assertNotRegexpMatches(html, r"data-block-type=[\"\']test_aside[\"\']")
        self.assertNotRegexpMatches(html, "Aside rendered")


@XBlock.needs("field-data")
@XBlock.needs("i18n")
@XBlock.needs("user")
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
        self.field_data = Mock()

    @XBlock.register_temp_plugin(PureXBlock, identifier='pure')
    @ddt.data("user", "i18n", "field-data")
    def test_expected_services_exist(self, expected_service):
        """
        Tests that the 'user' and 'i18n' services are provided by the Studio runtime.
        """
        descriptor = ItemFactory(category="pure", parent=self.course)
        runtime = _preview_module_system(
            self.request,
            descriptor,
            self.field_data,
        )
        service = runtime.service(descriptor, expected_service)
        self.assertIsNotNone(service)
