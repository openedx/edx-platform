import json
from mock import Mock
from pprint import pprint
import unittest


from xmodule.capa_module import CapaModule
from xmodule.modulestore import Location
from lxml import etree

from . import test_system

class CapaFactory(object):
    """
    A helper class to create problem modules with various parameters for testing.
    """

    sample_problem_xml = """<?xml version="1.0"?>
<problem>
  <text>
    <p>What is pi, to two decimal placs?</p>
  </text>
<numericalresponse answer="3.14">
<textline math="1" size="30"/>
</numericalresponse>
</problem>
"""

    num = 0
    @staticmethod
    def next_num():
        CapaFactory.num += 1
        return CapaFactory.num

    @staticmethod
    def create(graceperiod=None,
               due=None,
               max_attempts=None,
               showanswer=None,
               rerandomize=None,
               force_save_button=None,
               attempts=None,
               problem_state=None,
               ):
        """
        All parameters are optional, and are added to the created problem if specified.

        Arguments:
            graceperiod:
            due:
            max_attempts:
            showanswer:
            force_save_button:
            rerandomize: all strings, as specified in the policy for the problem

            problem_state: a dict to to be serialized into the instance_state of the
                module.

            attempts: also added to instance state.  Should be a number.
        """
        definition = {'data': CapaFactory.sample_problem_xml,}
        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(CapaFactory.next_num())])
        metadata = {}
        if graceperiod is not None:
            metadata['graceperiod'] = graceperiod
        if due is not None:
            metadata['due'] = due
        if max_attempts is not None:
            metadata['attempts'] = max_attempts
        if showanswer is not None:
            metadata['showanswer'] = showanswer
        if force_save_button is not None:
            metadata['force_save_button'] = force_save_button
        if rerandomize is not None:
            metadata['rerandomize'] = rerandomize


        descriptor = Mock(weight="1")
        instance_state_dict = {}
        if problem_state is not None:
            instance_state_dict = problem_state
        if attempts is not None:
            instance_state_dict['attempts'] = attempts
        if len(instance_state_dict) > 0:
            instance_state = json.dumps(instance_state_dict)
        else:
            instance_state = None

        module = CapaModule(test_system, location,
                            definition, descriptor,
                                      instance_state, None, metadata=metadata)

        return module



class CapaModuleTest(unittest.TestCase):

    def test_import(self):
        module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)

        other_module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)
        self.assertNotEqual(module.url_name, other_module.url_name,
                            "Factory should be creating unique names for each problem")

    def test_showanswer(self):
        """
        Make sure the show answer logic does the right thing.
        """
        # default, no due date, showanswer 'closed'
        problem = CapaFactory.create()
        pprint(problem.__dict__)
        self.assertFalse(problem.answer_available())
