"""
Tests for sequence module.
"""
# pylint: disable=no-member
from datetime import timedelta
from django.utils.timezone import now
from freezegun import freeze_time
from mock import Mock, patch
from xmodule.seq_module import SequenceModule
from xmodule.tests import get_test_system
from xmodule.tests.helpers import StubUserService
from xmodule.tests.xml import factories as xml, XModuleXmlImportTest
from xmodule.x_module import STUDENT_VIEW

TODAY = now()
DUE_DATE = TODAY + timedelta(days=7)
PAST_DUE_BEFORE_END_DATE = TODAY + timedelta(days=14)
COURSE_END_DATE = TODAY + timedelta(days=21)


class SequenceBlockTestCase(XModuleXmlImportTest):
    """
    Base class for tests of Sequence Module.
    """
    def setUp(self):
        super(SequenceBlockTestCase, self).setUp()

        course_xml = self._set_up_course_xml()
        self.course = self.process_xml(course_xml)
        self._set_up_module_system(self.course)

        for chapter_index in range(len(self.course.get_children())):
            chapter = self._set_up_block(self.course, chapter_index)
            setattr(self, 'chapter_{}'.format(chapter_index + 1), chapter)

            for sequence_index in range(len(chapter.get_children())):
                sequence = self._set_up_block(chapter, sequence_index)
                setattr(self, 'sequence_{}_{}'.format(chapter_index + 1, sequence_index + 1), sequence)

    @staticmethod
    def _set_up_course_xml():
        """
        Sets up and returns XML course structure.
        """
        course = xml.CourseFactory.build(end=str(COURSE_END_DATE))

        chapter_1 = xml.ChapterFactory.build(parent=course)  # has 2 child sequences
        xml.ChapterFactory.build(parent=course)  # has 0 child sequences
        chapter_3 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence
        chapter_4 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence, with hide_after_due

        xml.SequenceFactory.build(parent=chapter_1)
        xml.SequenceFactory.build(parent=chapter_1)
        sequence_3_1 = xml.SequenceFactory.build(parent=chapter_3)  # has 3 verticals
        xml.SequenceFactory.build(  # sequence_4_1
            parent=chapter_4,
            hide_after_due=str(True),
            due=str(DUE_DATE),
        )

        for _ in range(3):
            xml.VerticalFactory.build(parent=sequence_3_1)

        return course

    def _set_up_block(self, parent, index_in_parent):
        """
        Sets up the stub sequence module for testing.
        """
        block = parent.get_children()[index_in_parent]

        self._set_up_module_system(block)

        block.xmodule_runtime._services['bookmarks'] = Mock()  # pylint: disable=protected-access
        block.xmodule_runtime._services['user'] = StubUserService()  # pylint: disable=protected-access
        block.xmodule_runtime.xmodule_instance = getattr(block, '_xmodule', None)  # pylint: disable=protected-access
        block.parent = parent.location
        return block

    def _set_up_module_system(self, block):
        """
        Sets up the test module system for the given block.
        """
        module_system = get_test_system()
        module_system.descriptor_runtime = block._runtime  # pylint: disable=protected-access
        block.xmodule_runtime = module_system

    def _get_rendered_student_view(self, sequence, requested_child=None, extra_context=None, self_paced=False):
        """
        Returns the rendered student view for the given sequence and the
        requested_child parameter.
        """
        context = {'requested_child': requested_child}
        if extra_context:
            context.update(extra_context)

        # The render operation will ask modulestore for the current course to get some data. As these tests were
        # originally not written to be compatible with a real modulestore, we've mocked out the relevant return values.
        with patch.object(SequenceModule, '_get_course') as mock_course:
            self.course.self_paced = self_paced
            mock_course.return_value = self.course
            return sequence.xmodule_runtime.render(sequence, STUDENT_VIEW, context).content

    def _assert_view_at_position(self, rendered_html, expected_position):
        """
        Verifies that the rendered view contains the expected position.
        """
        self.assertIn("'position': {}".format(expected_position), rendered_html)

    def test_student_view_init(self):
        seq_module = SequenceModule(runtime=Mock(position=2), descriptor=Mock(), scope_ids=Mock())
        self.assertEquals(seq_module.position, 2)  # matches position set in the runtime

    def test_render_student_view(self):
        html = self._get_rendered_student_view(
            self.sequence_3_1,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
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

    def test_tooltip(self):
        html = self._get_rendered_student_view(self.sequence_3_1, requested_child=None)
        for child in self.sequence_3_1.children:
            self.assertIn("'page_title': '{}'".format(child.name), html)

    def test_hidden_content_before_due(self):
        html = self._get_rendered_student_view(self.sequence_4_1)
        self.assertIn("seq_module.html", html)
        self.assertIn("'banner_text': None", html)

    @freeze_time(COURSE_END_DATE)
    def test_hidden_content_past_due(self):
        progress_url = 'http://test_progress_link'
        html = self._get_rendered_student_view(
            self.sequence_4_1,
            extra_context=dict(progress_url=progress_url),
        )
        self.assertIn("hidden_content.html", html)
        self.assertIn(progress_url, html)

    @freeze_time(COURSE_END_DATE)
    def test_masquerade_hidden_content_past_due(self):
        html = self._get_rendered_student_view(
            self.sequence_4_1,
            extra_context=dict(specific_masquerade=True),
        )
        self.assertIn("seq_module.html", html)
        self.assertIn(
            "'banner_text': 'Because the due date has passed, "
            "this assignment is hidden from the learner.'",
            html
        )

    @freeze_time(PAST_DUE_BEFORE_END_DATE)
    def test_hidden_content_self_paced_past_due_before_end(self):
        html = self._get_rendered_student_view(self.sequence_4_1, self_paced=True)
        self.assertIn("seq_module.html", html)
        self.assertIn("'banner_text': None", html)

    @freeze_time(COURSE_END_DATE + timedelta(days=7))
    def test_hidden_content_self_paced_past_end(self):
        progress_url = 'http://test_progress_link'
        html = self._get_rendered_student_view(
            self.sequence_4_1,
            extra_context=dict(progress_url=progress_url),
            self_paced=True,
        )
        self.assertIn("hidden_content.html", html)
        self.assertIn(progress_url, html)
