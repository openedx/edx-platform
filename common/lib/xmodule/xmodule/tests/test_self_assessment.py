import json
from mock import Mock
import unittest

from xmodule.self_assessment_module import SelfAssessmentModule
from xmodule.modulestore import Location
from lxml import etree

from . import test_system

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

    metadata = {'attempts': '10'}

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
                'accept_file_upload' : False,
                }

        self.module = SelfAssessmentModule(test_system, self.location,
                                      self.definition, self.descriptor,
                                      static_data, state, metadata=self.metadata)

    def test_get_html(self):
        html = self.module.get_html(test_system)
        self.assertTrue("This is sample prompt text" in html)

    def test_self_assessment_flow(self):

        self.assertEqual(self.module.get_score()['score'], 0)

        self.module.save_answer({'student_answer': "I am an answer"}, test_system)
        self.assertEqual(self.module.state, self.module.ASSESSING)

        self.module.save_assessment({'assessment': '0'}, test_system)
        self.assertEqual(self.module.state, self.module.DONE)


        d = self.module.reset({})
        self.assertTrue(d['success'])
        self.assertEqual(self.module.state, self.module.INITIAL)

        # if we now assess as right, skip the REQUEST_HINT state
        self.module.save_answer({'student_answer': 'answer 4'}, test_system)
        self.module.save_assessment({'assessment': '1'}, test_system)
        self.assertEqual(self.module.state, self.module.DONE)

