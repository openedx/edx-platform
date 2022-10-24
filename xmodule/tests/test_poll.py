"""Test for Poll Xmodule functional logic."""

import json
import unittest

from unittest.mock import Mock

from opaque_keys.edx.keys import CourseKey
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xmodule.poll_module import PollBlock

from . import get_test_system
from .test_import import DummySystem


class PollBlockTest(unittest.TestCase):
    """Logic tests for Poll Xmodule."""

    raw_field_data = {
        'poll_answers': {'Yes': 1, 'Dont_know': 0, 'No': 0},
        'voted': False,
        'poll_answer': ''
    }

    def setUp(self):
        super().setUp()
        course_key = CourseKey.from_string('org/course/run')
        self.system = get_test_system(course_key)
        usage_key = course_key.make_usage_key(PollBlock.category, 'test_loc')
        # ScopeIds has 4 fields: user_id, block_type, def_id, usage_id
        scope_ids = ScopeIds(1, PollBlock.category, usage_key, usage_key)
        self.xmodule = PollBlock(
            self.system, DictFieldData(self.raw_field_data), scope_ids
        )

    def ajax_request(self, dispatch, data):
        """Call Xmodule.handle_ajax."""
        return json.loads(self.xmodule.handle_ajax(dispatch, data))

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
        assert total == 2
        self.assertDictEqual(callback, {'objectName': 'Conditional'})
        assert self.xmodule.poll_answer == 'No'

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

        output = PollBlock.from_xml(sample_poll_xml, module_system, id_generator)
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
        assert child_texts[(- 1)] == '< 18'
