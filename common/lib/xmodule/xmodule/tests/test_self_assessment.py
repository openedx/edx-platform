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
                  'hintprompt': 'Consider this...'}

    location = Location(["i4x", "edX", "sa_test", "selfassessment",
                         "SampleQuestion"])

    metadata = {}

    descriptor = Mock()

    def test_import(self):
        state = json.dumps({'student_answers': [],
                            'scores': [],
                            'hints': [],
                            'state': 'initial',
                            'attempts': 0})

        module = SelfAssessmentModule(test_system, self.location,
                                      self.definition, self.descriptor,
                                      state, {})

        self.assertEqual(module.get_score(), 0)
