"""
Tests for sequence module.
"""
# pylint: disable=no-member


import ast
import json
from datetime import timedelta

import ddt
import six
from django.utils.timezone import now
from freezegun import freeze_time
from mock import Mock, patch
from six.moves import range
from web_fragments.fragment import Fragment

from edx_toggles.toggles.testutils import override_waffle_flag
from common.djangoapps.student.tests.factories import UserFactory
from xmodule.seq_module import TIMED_EXAM_GATING_WAFFLE_FLAG, SequenceModule
from xmodule.tests import get_test_system
from xmodule.tests.helpers import StubUserService
from xmodule.tests.xml import XModuleXmlImportTest
from xmodule.tests.xml import factories as xml
from xmodule.x_module import PUBLIC_VIEW, STUDENT_VIEW

TODAY = now()
DUE_DATE = TODAY + timedelta(days=7)
PAST_DUE_BEFORE_END_DATE = TODAY + timedelta(days=14)
COURSE_END_DATE = TODAY + timedelta(days=21)


@ddt.ddt
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
        chapter_5 = xml.ChapterFactory.build(parent=course)  # has 1 child sequence, with a time limit

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

        sequence_5_1 = xml.SequenceFactory.build(
            parent=chapter_5,
            is_time_limited=str(True)
        )
        vertical_5_1 = xml.VerticalFactory.build(parent=sequence_5_1)
        xml.ProblemFactory.build(parent=vertical_5_1)

        return course

    def _set_up_block(self, parent, index_in_parent):
        """
        Sets up the stub sequence module for testing.
        """
        block = parent.get_children()[index_in_parent]

        self._set_up_module_system(block)

        block.xmodule_runtime._services['bookmarks'] = Mock()  # pylint: disable=protected-access
        block.xmodule_runtime._services['completion'] = Mock(  # pylint: disable=protected-access
            return_value=Mock(vertical_is_complete=Mock(return_value=True))
        )
        block.xmodule_runtime._services['user'] = StubUserService()  # pylint: disable=protected-access
        block.xmodule_runtime.xmodule_instance = getattr(block, '_xmodule', None)
        block.parent = parent.location
        return block

    def _set_up_module_system(self, block):
        """
        Sets up the test module system for the given block.
        """
        module_system = get_test_system()
        module_system.descriptor_runtime = block._runtime  # pylint: disable=protected-access
        block.xmodule_runtime = module_system

    def _get_rendered_view(self,
                           sequence,
                           requested_child=None,
                           extra_context=None,
                           self_paced=False,
                           view=STUDENT_VIEW):
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
            return sequence.xmodule_runtime.render(sequence, view, context).content

    def _assert_view_at_position(self, rendered_html, expected_position):
        """
        Verifies that the rendered view contains the expected position.
        """
        self.assertIn("'position': {}".format(expected_position), rendered_html)

    def test_student_view_init(self):
        seq_module = SequenceModule(runtime=Mock(position=2), descriptor=Mock(), scope_ids=Mock())
        self.assertEqual(seq_module.position, 2)  # matches position set in the runtime

    @ddt.unpack
    @ddt.data(
        {'view': STUDENT_VIEW},
        {'view': PUBLIC_VIEW},
    )
    def test_render_student_view(self, view):
        html = self._get_rendered_view(
            self.sequence_3_1,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
            view=view
        )
        self._assert_view_at_position(html, expected_position=1)
        self.assertIn(six.text_type(self.sequence_3_1.location), html)
        self.assertIn("'gated': False", html)
        self.assertIn("'next_url': 'NextSequential'", html)
        self.assertIn("'prev_url': 'PrevSequential'", html)
        self.assertNotIn("fa fa-check-circle check-circle is-hidden", html)

    @patch('xmodule.seq_module.User.objects.get', return_value=UserFactory.build())
    def test_timed_exam_gating_waffle_flag(self, mocked_user):
        """
        Verify the code inside the waffle flag is not executed with the flag off
        Verify the code inside the waffle flag is executed with the flag on
        """
        # the order of the overrides is important since the `assert_not_called` does
        # not appear to be limited to just the override_waffle_flag = False scope
        with override_waffle_flag(TIMED_EXAM_GATING_WAFFLE_FLAG, active=False):
            self._get_rendered_view(
                self.sequence_5_1,
                extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
                view=STUDENT_VIEW
            )
            mocked_user.assert_not_called()

        with override_waffle_flag(TIMED_EXAM_GATING_WAFFLE_FLAG, active=True):
            self._get_rendered_view(
                self.sequence_5_1,
                extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
                view=STUDENT_VIEW
            )
            mocked_user.assert_called_once()

    @override_waffle_flag(TIMED_EXAM_GATING_WAFFLE_FLAG, active=True)
    @patch('xmodule.seq_module.User.objects.get', return_value=UserFactory.build())
    def test_that_timed_sequence_gating_respects_access_configurations(self, mocked_user):  # pylint: disable=unused-argument
        """
        Verify that if a time limited sequence contains content type gated problems, we gate the sequence
        Verify that if a time limited sequence does not contain content type gated problems, we do not gate the sequence
        """
        # the one problem in this sequence needs to have graded set to true in order to test content type gating
        self.sequence_5_1.get_children()[0].get_children()[0].graded = True
        gated_fragment = Fragment('i_am_gated')

        # When a time limited sequence contains content type gated problems, the sequence itself is gated
        self.sequence_5_1.runtime._services['content_type_gating'] = Mock(return_value=Mock(  # pylint: disable=protected-access
            enabled_for_enrollment=Mock(return_value=True),
            content_type_gate_for_block=Mock(return_value=gated_fragment)
        ))
        view = self._get_rendered_view(
            self.sequence_5_1,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
            view=STUDENT_VIEW
        )
        self.assertIn('i_am_gated', view)
        # check a few elements to ensure the correct page was loaded
        self.assertIn("seq_module.html", view)
        self.assertIn('NextSequential', view)
        self.assertIn('PrevSequential', view)

        # When enabled_for_enrollment is false, the sequence itself is not gated
        self.sequence_5_1.runtime._services['content_type_gating'] = Mock(return_value=Mock(  # pylint: disable=protected-access
            enabled_for_enrollment=Mock(return_value=False),
            content_type_gate_for_block=Mock(return_value=gated_fragment)
        ))
        view = self._get_rendered_view(
            self.sequence_5_1,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
            view=STUDENT_VIEW
        )
        self.assertNotIn('i_am_gated', view)
        # check a few elements to ensure the correct page was loaded
        self.assertIn("seq_module.html", view)
        self.assertIn('NextSequential', view)
        self.assertIn('PrevSequential', view)

        # When content_type_gate_for_block returns None, the sequence itself is not gated
        self.sequence_5_1.runtime._services['content_type_gating'] = Mock(return_value=Mock(  # pylint: disable=protected-access
            enabled_for_enrollment=Mock(return_value=True),
            content_type_gate_for_block=Mock(return_value=None)
        ))
        view = self._get_rendered_view(
            self.sequence_5_1,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
            view=STUDENT_VIEW
        )
        self.assertNotIn('i_am_gated', view)
        # check a few elements to ensure the correct page was loaded
        self.assertIn("seq_module.html", view)
        self.assertIn('NextSequential', view)
        self.assertIn('PrevSequential', view)

    @ddt.unpack
    @ddt.data(
        {'view': STUDENT_VIEW},
        {'view': PUBLIC_VIEW},
    )
    def test_student_view_first_child(self, view):
        html = self._get_rendered_view(
            self.sequence_3_1, requested_child='first', view=view
        )
        self._assert_view_at_position(html, expected_position=1)

    @ddt.unpack
    @ddt.data(
        {'view': STUDENT_VIEW},
        {'view': PUBLIC_VIEW},
    )
    def test_student_view_last_child(self, view):
        html = self._get_rendered_view(self.sequence_3_1, requested_child='last', view=view)
        self._assert_view_at_position(html, expected_position=3)

    def test_tooltip(self):
        html = self._get_rendered_view(self.sequence_3_1, requested_child=None)
        for child in self.sequence_3_1.children:
            self.assertIn("'page_title': '{}'".format(child.block_id), html)

    def test_hidden_content_before_due(self):
        html = self._get_rendered_view(self.sequence_4_1)
        self.assertIn("seq_module.html", html)
        self.assertIn("'banner_text': None", html)

    def test_hidden_content_past_due(self):
        with freeze_time(COURSE_END_DATE):
            progress_url = 'http://test_progress_link'
            html = self._get_rendered_view(
                self.sequence_4_1,
                extra_context=dict(progress_url=progress_url),
            )
            self.assertIn("hidden_content.html", html)
            self.assertIn(progress_url, html)

    def test_masquerade_hidden_content_past_due(self):
        with freeze_time(COURSE_END_DATE):
            html = self._get_rendered_view(
                self.sequence_4_1,
                extra_context=dict(specific_masquerade=True),
            )
            self.assertIn("seq_module.html", html)
            html = self.get_context_dict_from_string(html)
            self.assertEqual(
                'Because the due date has passed, this assignment is hidden from the learner.',
                html['banner_text']
            )

    def test_hidden_content_self_paced_past_due_before_end(self):
        with freeze_time(PAST_DUE_BEFORE_END_DATE):
            html = self._get_rendered_view(self.sequence_4_1, self_paced=True)
            self.assertIn("seq_module.html", html)
            self.assertIn("'banner_text': None", html)

    def test_hidden_content_self_paced_past_end(self):
        with freeze_time(COURSE_END_DATE + timedelta(days=7)):
            progress_url = 'http://test_progress_link'
            html = self._get_rendered_view(
                self.sequence_4_1,
                extra_context=dict(progress_url=progress_url),
                self_paced=True,
            )
            self.assertIn("hidden_content.html", html)
            self.assertIn(progress_url, html)

    def _assert_gated(self, html, sequence):
        """
        Assert sequence content is gated
        """
        self.assertIn("seq_module.html", html)
        html = self.get_context_dict_from_string(html)
        self.assertIsNone(html['banner_text'])
        self.assertEqual([], html['items'])
        self.assertTrue(html['gated_content']['gated'])
        self.assertEqual('PrereqUrl', html['gated_content']['prereq_url'])
        self.assertEqual('PrereqSectionName', html['gated_content']['prereq_section_name'])
        self.assertIn(
            six.text_type(sequence.display_name),
            html['gated_content']['gated_section_name']
        )
        self.assertEqual('NextSequential', html['next_url'])
        self.assertEqual('PrevSequential', html['prev_url'])

    def _assert_prereq(self, html, sequence):
        """
        Assert sequence is a prerequisite with unfulfilled gates
        """
        self.assertIn("seq_module.html", html)
        html = self.get_context_dict_from_string(html)
        self.assertEqual(
            "This section is a prerequisite. You must complete this section in order to unlock additional content.",
            html['banner_text']
        )
        self.assertFalse(html['gated_content']['gated'])
        self.assertEqual(six.text_type(sequence.location), html['item_id'])
        self.assertIsNone(html['gated_content']['prereq_url'])
        self.assertIsNone(html['gated_content']['prereq_section_name'])
        self.assertEqual('NextSequential', html['next_url'])
        self.assertEqual('PrevSequential', html['prev_url'])

    def _assert_ungated(self, html, sequence):
        """
        Assert sequence is not gated
        """
        self.assertIn("seq_module.html", html)
        self.assertIn("'banner_text': None", html)
        self.assertIn("'gated': False", html)
        self.assertIn(six.text_type(sequence.location), html)
        self.assertIn("'prereq_url': None", html)
        self.assertIn("'prereq_section_name': None", html)
        self.assertIn("'next_url': 'NextSequential'", html)
        self.assertIn("'prev_url': 'PrevSequential'", html)

    def test_gated_content(self):
        """
        Test when sequence is both a prerequisite for a sequence
        and gated on another prerequisite sequence
        """
        # setup seq_1_2 as a gate and gated
        gating_mock_1_2 = Mock()
        gating_mock_1_2.return_value.is_gate_fulfilled.return_value = False
        gating_mock_1_2.return_value.required_prereq.return_value = True
        gating_mock_1_2.return_value.compute_is_prereq_met.return_value = [
            False,
            {'url': 'PrereqUrl', 'display_name': 'PrereqSectionName', 'id': 'mockId'}
        ]
        self.sequence_1_2.xmodule_runtime._services['gating'] = gating_mock_1_2  # pylint: disable=protected-access
        self.sequence_1_2.display_name = 'sequence_1_2'

        html = self._get_rendered_view(
            self.sequence_1_2,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
        )

        # expect content to be gated, with no banner
        self._assert_gated(html, self.sequence_1_2)

        # change seq_1_2 to be ungated, but still a gate (prequiste)
        gating_mock_1_2.return_value.is_gate_fulfilled.return_value = False
        gating_mock_1_2.return_value.required_prereq.return_value = True
        gating_mock_1_2.return_value.compute_is_prereq_met.return_value = [True, {}]

        html = self._get_rendered_view(
            self.sequence_1_2,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
        )
        # assert that content and preq banner is shown
        self._assert_prereq(html, self.sequence_1_2)

        # change seq_1_2 to have no unfulfilled gates
        gating_mock_1_2.return_value.is_gate_fulfilled.return_value = True
        gating_mock_1_2.return_value.required_prereq.return_value = True
        gating_mock_1_2.return_value.compute_is_prereq_met.return_value = [True, {}]

        html = self._get_rendered_view(
            self.sequence_1_2,
            extra_context=dict(next_url='NextSequential', prev_url='PrevSequential'),
        )

        # assert content shown as normal
        self._assert_ungated(html, self.sequence_1_2)

    def test_handle_ajax_get_completion_success(self):
        """
        Test that the completion data is returned successfully on
        targeted vertical through ajax call
        """
        for child in self.sequence_3_1.get_children():
            usage_key = six.text_type(child.location)
            completion_return = json.loads(self.sequence_3_1.handle_ajax(
                'get_completion',
                {'usage_key': usage_key}
            ))
            self.assertIsNot(completion_return, None)
            self.assertTrue('complete' in completion_return)
            self.assertEqual(completion_return['complete'], True)

    def test_handle_ajax_get_completion_return_none(self):
        """
        Test that the completion data is returned successfully None
        when usage key is None through ajax call
        """
        usage_key = None
        completion_return = self.sequence_3_1.handle_ajax(
            'get_completion',
            {'usage_key': usage_key}
        )
        self.assertIs(completion_return, None)

    def test_handle_ajax_metadata(self):
        """
        Test that the sequence metadata is returned from the
        metadata ajax handler.
        """
        # rather than dealing with json serialization of the Mock object,
        # let's just disable the bookmarks service
        self.sequence_3_1.xmodule_runtime._services['bookmarks'] = None
        metadata = json.loads(self.sequence_3_1.handle_ajax('metadata', {}))
        self.assertEqual(len(metadata['items']), 3)
        self.assertEqual(metadata['tag'], 'sequential')
        self.assertEqual(metadata['display_name'], self.sequence_3_1.display_name_with_default)

    def get_context_dict_from_string(self, data):
        """
        Retrieve dictionary from string.
        """
        # Replace tuple and un-necessary info from inside string and get the dictionary.
        cleaned_data = data.replace("(('seq_module.html',\n", '').replace("),\n {})", '').strip()
        return ast.literal_eval(cleaned_data)
