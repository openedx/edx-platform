"""
Tests for vertical module.
"""
import ddt
from mock import Mock
from fs.memoryfs import MemoryFS
from xmodule.tests import get_test_system
from xmodule.tests.helpers import StubUserService
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml
from xmodule.x_module import STUDENT_VIEW, AUTHOR_VIEW


class BaseVerticalBlockTest(XModuleXmlImportTest):
    """
    Tests for the BaseVerticalBlock.
    """
    test_html_1 = 'Test HTML 1'
    test_html_2 = 'Test HTML 2'

    def setUp(self):
        super(BaseVerticalBlockTest, self).setUp()
        # construct module
        course = xml.CourseFactory.build()
        sequence = xml.SequenceFactory.build(parent=course)
        vertical = xml.VerticalFactory.build(parent=sequence)

        self.course = self.process_xml(course)
        xml.HtmlFactory(parent=vertical, url_name='test-html-1', text=self.test_html_1)
        xml.HtmlFactory(parent=vertical, url_name='test-html-2', text=self.test_html_2)

        self.course = self.process_xml(course)
        course_seq = self.course.get_children()[0]
        self.module_system = get_test_system()

        self.module_system.descriptor_runtime = self.course._runtime  # pylint: disable=protected-access
        self.course.runtime.export_fs = MemoryFS()

        self.vertical = course_seq.get_children()[0]
        self.vertical.xmodule_runtime = self.module_system

        self.username = "bilbo"
        self.default_context = {"bookmarked": False, "username": self.username}


@ddt.ddt
class VerticalBlockTestCase(BaseVerticalBlockTest):
    """
    Tests for the VerticalBlock.
    """
    def assert_bookmark_info_in(self, content):
        """
        Assert content has all the bookmark info.
        """
        self.assertIn('bookmark_id', content)
        self.assertIn('{},{}'.format(self.username, unicode(self.vertical.location)), content)
        self.assertIn('bookmarked', content)
        self.assertIn('show_bookmark_button', content)

    @ddt.unpack
    @ddt.data(
        {'context': None},
        {'context': {}}
    )
    def test_render_student_view(self, context):
        """
        Test the rendering of the student view.
        """
        self.module_system._services['bookmarks'] = Mock()  # pylint: disable=protected-access
        self.module_system._services['user'] = StubUserService()  # pylint: disable=protected-access

        html = self.module_system.render(
            self.vertical, STUDENT_VIEW, self.default_context if context is None else context
        ).content
        self.assertIn(self.test_html_1, html)
        self.assertIn(self.test_html_2, html)
        self.assert_bookmark_info_in(html)

    def test_render_studio_view(self):
        """
        Test the rendering of the Studio author view
        """
        # Vertical shouldn't render children on the unit page
        context = {
            'is_unit_page': True
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        self.assertNotIn(self.test_html_1, html)
        self.assertNotIn(self.test_html_2, html)

        # Vertical should render reorderable children on the container page
        reorderable_items = set()
        context = {
            'is_unit_page': False,
            'reorderable_items': reorderable_items,
        }
        html = self.module_system.render(self.vertical, AUTHOR_VIEW, context).content
        self.assertIn(self.test_html_1, html)
        self.assertIn(self.test_html_2, html)
