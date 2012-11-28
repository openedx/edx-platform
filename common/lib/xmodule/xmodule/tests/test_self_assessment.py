import json
from mock import Mock
import unittest

from xmodule.self_assessment_module import SelfAssessmentModule
from xmodule.modulestore import Location

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
                            'state': SelfAssessmentModule.ASSESSING,
                            'attempts': 2})

        module = SelfAssessmentModule(test_system, self.location,
                                      self.definition, self.descriptor,
                                      state, {}, metadata=self.metadata)

        self.assertEqual(module.get_score(), 1)


        self.assertTrue('answer 3' in module.get_html())
        self.assertFalse('answer 2' in module.get_html())

        module.save_assessment({'assessment': '0'})
        self.assertEqual(module.state, module.REQUEST_HINT)

        module.save_hint({'hint': 'hint for ans 3'})
        self.assertEqual(module.state, module.DONE)

        d = module.reset({})
        self.assertTrue(d['success'])
        self.assertEqual(module.state, module.INITIAL)

        # if we now assess as right, skip the REQUEST_HINT state
        module.save_answer({'student_answer': 'answer 4'})
        module.save_assessment({'assessment': '1'})
        self.assertEqual(module.state, module.DONE)
