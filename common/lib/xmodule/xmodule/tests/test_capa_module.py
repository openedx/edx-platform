import datetime
import json
from mock import Mock, patch
from pprint import pprint
import unittest

import xmodule
import capa
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
    def input_key():
        """ Return the input key to use when passing GET parameters """
        return ("input_" + 
                "-".join(['i4x', 'edX', 'capa_test', 'problem', 
                        'SampleProblem%d' % CapaFactory.num]) +
                "_2_1")

    @staticmethod
    def create(graceperiod=None,
               due=None,
               max_attempts=None,
               showanswer=None,
               rerandomize=None,
               force_save_button=None,
               attempts=None,
               problem_state=None,
               correct=False
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
        definition = {'data': CapaFactory.sample_problem_xml, }
        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem%d" % CapaFactory.next_num()])
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

        if correct:
            # TODO: probably better to actually set the internal state properly, but...
            module.get_score = lambda: {'score': 1, 'total': 1}

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


    def test_correct(self):
        """
        Check that the factory creates correct and incorrect problems properly.
        """
        module = CapaFactory.create()
        self.assertEqual(module.get_score()['score'], 0)

        other_module = CapaFactory.create(correct=True)
        self.assertEqual(other_module.get_score()['score'], 1)


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

        # can't see after attempts used up, even with due date in the future
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

    def test_showanswer_finished(self):
        """
        With showanswer="finished" should show answer after the problem is closed,
        or after the answer is correct.
        """

        # can see after attempts used up, even with due date in the future
        used_all_attempts = CapaFactory.create(showanswer='finished',
                                               max_attempts="1",
                                               attempts="1",
                                               due=self.tomorrow_str)
        self.assertTrue(used_all_attempts.answer_available())


        # can see after due date
        past_due_date = CapaFactory.create(showanswer='finished',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.yesterday_str)
        self.assertTrue(past_due_date.answer_available())


        # can't see because attempts left and wrong
        attempts_left_open = CapaFactory.create(showanswer='finished',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.tomorrow_str)
        self.assertFalse(attempts_left_open.answer_available())

        # _can_ see because attempts left and right
        correct_ans = CapaFactory.create(showanswer='finished',
                                               max_attempts="1",
                                               attempts="0",
                                               due=self.tomorrow_str,
                                               correct=True)
        self.assertTrue(correct_ans.answer_available())


        # Can see even though grace period hasn't expired, because have no more
        # attempts.
        still_in_grace = CapaFactory.create(showanswer='finished',
                                            max_attempts="1",
                                            attempts="1",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        self.assertTrue(still_in_grace.answer_available())


    def test_parse_get_params(self):

        # Valid GET param dict
        valid_get_dict = {'input_1': 'test',
                        'input_1_2': 'test',
                        'input_1_2_3': 'test',
                        'input_[]_3': 'test',
                        'input_4': None,
                        'input_5': [],
                        'input_6': 5}
        
        result = CapaModule.make_dict_of_responses(valid_get_dict)

        # Expect that we get a dict with "input" stripped from key names
        # and that we get the same values back
        for key in result.keys():
            original_key = "input_" + key
            self.assertTrue(original_key in valid_get_dict,
                            "Output dict should have key %s" % original_key)
            self.assertEqual(valid_get_dict[original_key], result[key])


        # Valid GET param dict with list keys
        valid_get_dict = {'input_2[]': ['test1', 'test2']}
        result = CapaModule.make_dict_of_responses(valid_get_dict)
        self.assertTrue('2' in result)
        self.assertEqual(valid_get_dict['input_2[]'], result['2'])

        # If we use [] at the end of a key name, we should always
        # get a list, even if there's just one value
        valid_get_dict = {'input_1[]': 'test'}
        result = CapaModule.make_dict_of_responses(valid_get_dict)
        self.assertEqual(result['1'], ['test'])


        # If we have no underscores in the name, then the key is invalid
        invalid_get_dict = {'input': 'test'}
        with self.assertRaises(ValueError):
            result = CapaModule.make_dict_of_responses(invalid_get_dict)


        # Two equivalent names (one list, one non-list)
        # One of the values would overwrite the other, so detect this
        # and raise an exception
        invalid_get_dict = {'input_1[]': 'test 1',
                            'input_1': 'test 2' }
        with self.assertRaises(ValueError):
            result = CapaModule.make_dict_of_responses(invalid_get_dict)

    def test_check_problem_correct(self):

        module = CapaFactory.create(attempts=1)

        # Simulate that all answers are marked correct, no matter
        # what the input is, by patching CorrectMap.is_correct()
        with patch('capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = True

            # Check the problem
            get_request_dict = { CapaFactory.input_key(): '3.14' }
            result = module.check_problem(get_request_dict)

        # Expect that the problem is marked correct
        self.assertEqual(result['success'], 'correct')

        # Expect that the number of attempts is incremented by 1
        self.assertEqual(module.attempts, 2)


    def test_check_problem_incorrect(self):

        module = CapaFactory.create(attempts=0)

        # Simulate marking the input incorrect
        with patch('capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = False

            # Check the problem
            get_request_dict = { CapaFactory.input_key(): '0' }
            result = module.check_problem(get_request_dict)

        # Expect that the problem is marked correct
        self.assertEqual(result['success'], 'incorrect')

        # Expect that the number of attempts is incremented by 1
        self.assertEqual(module.attempts, 1)


    def test_check_problem_closed(self):
        module = CapaFactory.create(attempts=3)

        # Problem closed -- cannot submit
        # Simulate that CapaModule.closed() always returns True
        with patch('xmodule.capa_module.CapaModule.closed') as mock_closed:
            mock_closed.return_value = True
            with self.assertRaises(xmodule.exceptions.NotFoundError):
                get_request_dict = { CapaFactory.input_key(): '3.14' }
                module.check_problem(get_request_dict)

        # Expect that number of attempts NOT incremented
        self.assertEqual(module.attempts, 3)


    def test_check_problem_resubmitted_with_randomize(self):
        # Randomize turned on
        module = CapaFactory.create(rerandomize='always', attempts=0)

        # Simulate that the problem is completed
        module.lcp.done = True

        # Expect that we cannot submit
        with self.assertRaises(xmodule.exceptions.NotFoundError):
            get_request_dict = { CapaFactory.input_key(): '3.14' }
            module.check_problem(get_request_dict)

        # Expect that number of attempts NOT incremented
        self.assertEqual(module.attempts, 0)


    def test_check_problem_resubmitted_no_randomize(self):
        # Randomize turned off
        module = CapaFactory.create(rerandomize='never', attempts=0)

        # Simulate that the problem is completed
        module.lcp.done = True

        # Expect that we can submit successfully
        get_request_dict = { CapaFactory.input_key(): '3.14' }
        result = module.check_problem(get_request_dict)

        self.assertEqual(result['success'], 'correct')

        # Expect that number of attempts IS incremented
        self.assertEqual(module.attempts, 1)


    def test_check_problem_queued(self):
        module = CapaFactory.create(attempts=1)

        # Simulate that the problem is queued
        with patch('capa.capa_problem.LoncapaProblem.is_queued') \
                as mock_is_queued,\
            patch('capa.capa_problem.LoncapaProblem.get_recentmost_queuetime') \
                as mock_get_queuetime:

            mock_is_queued.return_value = True
            mock_get_queuetime.return_value = datetime.datetime.now()
        
            get_request_dict = { CapaFactory.input_key(): '3.14' }
            result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            self.assertTrue('You must wait' in result['success'])

        # Expect that the number of attempts is NOT incremented
        self.assertEqual(module.attempts, 1)


    def test_check_problem_student_input_error(self):
        module = CapaFactory.create(attempts=1)

        # Simulate a student input exception
        with patch('capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
            mock_grade.side_effect = capa.responsetypes.StudentInputError('test error')

            get_request_dict = { CapaFactory.input_key(): '3.14' }
            result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            self.assertTrue('test error' in result['success'])

        # Expect that the number of attempts is NOT incremented
        self.assertEqual(module.attempts, 1)
