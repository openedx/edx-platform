import json
from mock import Mock
import unittest

from xmodule.self_assessment_module import SelfAssessmentModule
from xmodule.modulestore import Location
from lxml import etree

from . import test_system

class SelfAssessmentTest(unittest.TestCase):

    definition = {'rubric': 'A rubric',
                  'prompt': 'Who?',
                  'submitmessage': 'Shall we submit now?',
                  'hintprompt': 'Consider this...',
                  }

    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

    metadata = {'attempts': '10'}

    descriptor = Mock()

    def test_import(self):
        state = json.dumps({'student_answers': ["Answer 1", "answer 2", "answer 3"],
                            'scores': [0, 1],
                            'hints': ['o hai'],
                            'state': SelfAssessmentModule.INITIAL,
                            'attempts': 2})

        rubric = '''<rubric><rubric>
            <category>
			<description>Response Quality</description>
			<option>The response is not a satisfactory answer to the question.  It either fails to address the question or does so in a limited way, with no evidence of higher-order thinking.</option>
		    </category>
             </rubric></rubric>'''

        prompt = etree.XML("<prompt>Text</prompt>")
        static_data = {
                'max_attempts': 10,
                'rubric': etree.XML(rubric),
                'prompt': prompt,
                'max_score': 1
                }

        module = SelfAssessmentModule(test_system, self.location,
                                      self.definition, self.descriptor,
                                      static_data, state, metadata=self.metadata)

        self.assertEqual(module.get_score()['score'], 0)


        module.save_answer({'student_answer': "I am an answer"}, test_system)
        self.assertEqual(module.state, module.ASSESSING)

        module.save_assessment({'assessment': '0'}, test_system)
        self.assertEqual(module.state, module.POST_ASSESSMENT)
        module.save_hint({'hint': 'this is a hint'}, test_system)
        self.assertEqual(module.state, module.DONE)

        d = module.reset({})
        self.assertTrue(d['success'])
        self.assertEqual(module.state, module.INITIAL)

        # if we now assess as right, skip the REQUEST_HINT state
        module.save_answer({'student_answer': 'answer 4'}, test_system)
        module.save_assessment({'assessment': '1'}, test_system)
        self.assertEqual(module.state, module.DONE)
