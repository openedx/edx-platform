# -*- coding: utf-8 -*-
"""Test for Poll Xmodule functional logic."""
from mock import Mock

from xmodule.poll_module import PollDescriptor
from . import LogicTest
from .test_import import DummySystem


class PollModuleTest(LogicTest):
    """Logic tests for Poll Xmodule."""
    descriptor_class = PollDescriptor
    raw_field_data = {
        'poll_answers': {'Yes': 1, 'Dont_know': 0, 'No': 0},
        'voted': False,
        'poll_answer': ''
    }

    def test_bad_ajax_request(self):
        # Make sure that answer for incorrect request is error json.
        response = self.ajax_request('bad_answer', {})
        self.assertDictEqual(response, {'error': 'Unknown Command!'})

    def test_good_ajax_request(self):
        # Make sure that ajax request works correctly.
        response = self.ajax_request('No', {})

        poll_answers = response['poll_answers']
        total = response['total']
        callback = response['callback']

        self.assertDictEqual(poll_answers, {'Yes': 1, 'Dont_know': 0, 'No': 1})
        self.assertEqual(total, 2)
        self.assertDictEqual(callback, {'objectName': 'Conditional'})
        self.assertEqual(self.xmodule.poll_answer, 'No')

    def test_poll_export_with_unescaped_characters_xml(self):
        """
        Make sure that poll_module will export fine if its xml contains
        unescaped characters.
        """
        module_system = DummySystem(load_error_modules=True)
        id_generator = Mock()
        id_generator.target_course_id = self.xmodule.course_id
        sample_poll_xml = '''
        <poll_question display_name="Poll Question">
            <p>How old are you?</p>
            <answer id="less18">18</answer>
        </poll_question>
        '''

        output = PollDescriptor.from_xml(sample_poll_xml, module_system, id_generator)
        # Update the answer with invalid character.
        invalid_characters_poll_answer = output.answers[0]
        # Invalid less-than character.
        invalid_characters_poll_answer['text'] = '< 18'
        output.answers[0] = invalid_characters_poll_answer
        output.save()

        xml = output.definition_to_xml(None)
        # Extract texts of all children.
        child_texts = xml.xpath('//text()')
        # Last index of child_texts contains text of answer tag.
        self.assertEqual(child_texts[-1], '< 18')
