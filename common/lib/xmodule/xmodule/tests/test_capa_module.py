import datetime
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

            attempts: also added to instance state.  Will be converted to an int.
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
            # converting to int here because I keep putting "0" and "1" in the tests
            # since everything else is a string.
            instance_state_dict['attempts'] = int(attempts)
        if len(instance_state_dict) > 0:
            instance_state = json.dumps(instance_state_dict)
        else:
            instance_state = None

        module = CapaModule(test_system, location,
                            definition, descriptor,
                                      instance_state, None, metadata=metadata)

        return module



class CapaModuleTest(unittest.TestCase):


    def setUp(self):
        now = datetime.datetime.now()
        day_delta = datetime.timedelta(days=1)
        self.yesterday_str = str(now - day_delta)
        self.today_str = str(now)
        self.tomorrow_str = str(now + day_delta)

        # in the capa grace period format, not in time delta format
        self.two_day_delta_str = "2 days"

    def test_import(self):
        module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)

        other_module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)
        self.assertNotEqual(module.url_name, other_module.url_name,
                            "Factory should be creating unique names for each problem")

    def test_showanswer_default(self):
        """
        Make sure the show answer logic does the right thing.
        """
        # default, no due date, showanswer 'closed', so problem is open, and show_answer
        # not visible.
        problem = CapaFactory.create()
        self.assertFalse(problem.answer_available())


    def test_showanswer_attempted(self):
        problem = CapaFactory.create(showanswer='attempted')
        self.assertFalse(problem.answer_available())
        problem.attempts = 1
        self.assertTrue(problem.answer_available())


    def test_showanswer_closed(self):

        # can see after attempts used up, even with due date in the future
        used_all_attempts = CapaFactory.create(showanswer='closed',
                                               max_attempts="1",
                                               attempts="1",
                                               due=self.tomorrow_str)
        self.assertTrue(used_all_attempts.answer_available())


        # can see after due date
        after_due_date = CapaFactory.create(showanswer='closed',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.yesterday_str)
        self.assertTrue(after_due_date.answer_available())


        # can't see because attempts left
        attempts_left_open = CapaFactory.create(showanswer='closed',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.tomorrow_str)
        self.assertFalse(attempts_left_open.answer_available())

        # Can't see because grace period hasn't expired
        still_in_grace = CapaFactory.create(showanswer='closed',
                                            max_attempts="1",
                                            attempts="0",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        self.assertFalse(still_in_grace.answer_available())



    def test_showanswer_past_due(self):
        """
        With showanswer="past_due" should only show answer after the problem is closed
        for everyone--e.g. after due date + grace period.
        """

        # can see after attempts used up, even with due date in the future
        used_all_attempts = CapaFactory.create(showanswer='past_due',
                                               max_attempts="1",
                                               attempts="1",
                                               due=self.tomorrow_str)
        self.assertFalse(used_all_attempts.answer_available())


        # can see after due date
        past_due_date = CapaFactory.create(showanswer='past_due',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.yesterday_str)
        self.assertTrue(past_due_date.answer_available())


        # can't see because attempts left
        attempts_left_open = CapaFactory.create(showanswer='past_due',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.tomorrow_str)
        self.assertFalse(attempts_left_open.answer_available())

        # Can't see because grace period hasn't expired, even though have no more
        # attempts.
        still_in_grace = CapaFactory.create(showanswer='past_due',
                                            max_attempts="1",
                                            attempts="1",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        self.assertFalse(still_in_grace.answer_available())





