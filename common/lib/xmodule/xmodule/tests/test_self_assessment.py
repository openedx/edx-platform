import json
from mock import Mock, MagicMock
import unittest

from xmodule.open_ended_grading_classes.self_assessment_module import SelfAssessmentModule
from xmodule.modulestore import Location
from lxml import etree

from . import get_test_system

import test_util_open_ended


class SelfAssessmentTest(unittest.TestCase):
    rubric = '''<rubric><rubric>
        <category>
        <description>Response Quality</description>
        <option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
        </category>
         </rubric></rubric>'''

    prompt = etree.XML("<prompt>This is sample prompt text.</prompt>")
    definition = {'rubric': rubric,
                  'prompt': prompt,
                  'submitmessage': 'Shall we submit now?',
                  'hintprompt': 'Consider this...',
    }

    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

    descriptor = Mock()

    def setUp(self):
        state = json.dumps({'student_answers': ["Answer 1", "answer 2", "answer 3"],
                            'scores': [0, 1],
                            'hints': ['o hai'],
                            'state': SelfAssessmentModule.INITIAL,
                            'attempts': 2})

        static_data = {
            'max_attempts': 10,
            'rubric': etree.XML(self.rubric),
            'prompt': self.prompt,
            'max_score': 1,
            'display_name': "Name",
            'accept_file_upload': False,
            'close_date': None,
            's3_interface': test_util_open_ended.S3_INTERFACE,
            'open_ended_grading_interface': test_util_open_ended.OPEN_ENDED_GRADING_INTERFACE,
            'skip_basic_checks': False,
        }

        self.module = SelfAssessmentModule(get_test_system(), self.location,
                                           self.definition,
                                           self.descriptor,
                                           static_data)

    def test_get_html(self):
        html = self.module.get_html(self.module.system)
        self.assertTrue("This is sample prompt text" in html)

    def test_self_assessment_flow(self):
        responses = {'assessment': '0', 'score_list[]': ['0', '0']}

        def get_fake_item(name):
            return responses[name]

        def get_data_for_location(self, location, student):
            return {
                'count_graded': 0,
                'count_required': 0,
                'student_sub_count': 0,
            }

        mock_query_dict = MagicMock()
        mock_query_dict.__getitem__.side_effect = get_fake_item
        mock_query_dict.getlist = get_fake_item

        self.module.peer_gs.get_data_for_location = get_data_for_location

        self.assertEqual(self.module.get_score()['score'], 0)

        self.module.save_answer({'student_answer': "I am an answer"},
                                self.module.system)
        self.assertEqual(self.module.child_state, self.module.ASSESSING)

        self.module.save_assessment(mock_query_dict, self.module.system)
        self.assertEqual(self.module.child_state, self.module.DONE)

        d = self.module.reset({})
        self.assertTrue(d['success'])
        self.assertEqual(self.module.child_state, self.module.INITIAL)

        # if we now assess as right, skip the REQUEST_HINT state
        self.module.save_answer({'student_answer': 'answer 4'},
                                self.module.system)
        responses['assessment'] = '1'
        self.module.save_assessment(mock_query_dict, self.module.system)
        self.assertEqual(self.module.child_state, self.module.DONE)
