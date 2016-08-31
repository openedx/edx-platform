"""
Tests for sequence module.
"""
# pylint: disable=no-member
import ddt
from mock import Mock
from xmodule.tests import get_test_system
from xmodule.tests.helpers import StubUserService
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml
from xmodule.x_module import STUDENT_VIEW
from xmodule.seq_module import SequenceModule


@ddt.ddt
class SequenceBlockTestCase(XModuleXmlImportTest):
    """
    Tests for the Sequence Module.
    """
    @classmethod
    def setUpClass(cls):
        super(SequenceBlockTestCase, cls).setUpClass()

        course_xml = cls._set_up_course_xml()
        cls.course = cls.process_xml(course_xml)
        cls._set_up_module_system(cls.course)

        for chapter_index in range(len(cls.course.get_children())):
            chapter = cls._set_up_block(cls.course, chapter_index)
            setattr(cls, 'chapter_{}'.format(chapter_index + 1), chapter)

            for sequence_index in range(len(chapter.get_children())):
                sequence = cls._set_up_block(chapter, sequence_index)
                setattr(cls, 'sequence_{}_{}'.format(chapter_index + 1, sequence_index + 1), sequence)

    @classmethod
    def _set_up_course_xml(cls):
        """
        Sets up and returns XML course structure.
        """
        course = xml.CourseFactory.build()

        chapter_1 = xml.ChapterFactory.build(parent=course)  # has 2 child sequences
        xml.ChapterFactory.build(parent=course)  # has 0 child sequences
        chapter_3 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence
        chapter_4 = xml.ChapterFactory.build(parent=course)  # has 2 child sequences

        xml.SequenceFactory.build(parent=chapter_1)
        xml.SequenceFactory.build(parent=chapter_1)
        sequence_3_1 = xml.SequenceFactory.build(parent=chapter_3)  # has 3 verticals
        xml.SequenceFactory.build(parent=chapter_4)
        xml.SequenceFactory.build(parent=chapter_4)

        for _ in range(3):
            xml.VerticalFactory.build(parent=sequence_3_1)

        return course

    @classmethod
    def _set_up_block(cls, parent, index_in_parent):
        """
        Sets up the stub sequence module for testing.
        """
        block = parent.get_children()[index_in_parent]

        cls._set_up_module_system(block)

        block.xmodule_runtime._services['bookmarks'] = Mock()  # pylint: disable=protected-access
        block.xmodule_runtime._services['user'] = StubUserService()  # pylint: disable=protected-access
        block.xmodule_runtime.xmodule_instance = getattr(block, '_xmodule', None)  # pylint: disable=protected-access
        block.parent = parent.location
        return block

    @classmethod
    def _set_up_module_system(cls, block):
        """
        Sets up the test module system for the given block.
        """
        module_system = get_test_system()
        module_system.descriptor_runtime = block._runtime  # pylint: disable=protected-access
        block.xmodule_runtime = module_system

    def test_student_view_init(self):
        seq_module = SequenceModule(runtime=Mock(position=2), descriptor=Mock(), scope_ids=Mock())
        self.assertEquals(seq_module.position, 2)  # matches position set in the runtime

    def test_render_student_view(self):
        html = self._get_rendered_student_view(
            self.sequence_3_1,
            requested_child=None,
            next_url='NextSequential',
            prev_url='PrevSequential'
        )
        self._assert_view_at_position(html, expected_position=1)
        self.assertIn(unicode(self.sequence_3_1.location), html)
        self.assertIn("'next_url': 'NextSequential'", html)
        self.assertIn("'prev_url': 'PrevSequential'", html)

    def test_student_view_first_child(self):
        html = self._get_rendered_student_view(self.sequence_3_1, requested_child='first')
        self._assert_view_at_position(html, expected_position=1)

    def test_student_view_last_child(self):
        html = self._get_rendered_student_view(self.sequence_3_1, requested_child='last')
        self._assert_view_at_position(html, expected_position=3)

    def _get_rendered_student_view(self, sequence, requested_child, next_url=None, prev_url=None):
        """
        Returns the rendered student view for the given sequence and the
        requested_child parameter.
        """
        return sequence.xmodule_runtime.render(
            sequence,
            STUDENT_VIEW,
            {
                'requested_child': requested_child,
                'next_url': next_url,
                'prev_url': prev_url,
            },
        ).content

    def _assert_view_at_position(self, rendered_html, expected_position):
        """
        Verifies that the rendered view contains the expected position.
        """
        self.assertIn("'position': {}".format(expected_position), rendered_html)

    def test_tooltip(self):
        html = self._get_rendered_student_view(self.sequence_3_1, requested_child=None)
        for child in self.sequence_3_1.children:
            self.assertIn("'page_title': '{}'".format(child.name), html)
