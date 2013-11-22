# -*- coding: utf-8 -*-
"""
Tests of the Capa XModule
"""
#pylint: disable=C0111
#pylint: disable=R0904
#pylint: disable=C0103
#pylint: disable=C0302

import datetime
import json
import random
import textwrap
import unittest

from mock import Mock, patch
from webob.multidict import MultiDict

import xmodule
from capa.responsetypes import (StudentInputError, LoncapaProblemError,
                                ResponseError)
from xmodule.capa_module import CapaModule, ComplexEncoder
from xmodule.modulestore import Location
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from . import get_test_system
from pytz import UTC
from capa.correctmap import CorrectMap


class CapaFactory(object):
    """
    A helper class to create problem modules with various parameters for testing.
    """

    sample_problem_xml = textwrap.dedent("""\
        <?xml version="1.0"?>
        <problem>
            <text>
                <p>What is pi, to two decimal places?</p>
            </text>
        <numericalresponse answer="3.14">
        <textline math="1" size="30"/>
        </numericalresponse>
        </problem>
    """)

    num = 0

    @classmethod
    def next_num(cls):
        cls.num += 1
        return cls.num

    @classmethod
    def input_key(cls, input_num=2):
        """
        Return the input key to use when passing GET parameters
        """
        return ("input_" + cls.answer_key(input_num))

    @classmethod
    def answer_key(cls, input_num=2):
        """
        Return the key stored in the capa problem answer dict
        """
        return (
            "%s_%d_1" % (
                "-".join(['i4x', 'edX', 'capa_test', 'problem', 'SampleProblem%d' % cls.num]),
                input_num,
            )
        )

    @classmethod
    def create(cls,
               graceperiod=None,
               due=None,
               max_attempts=None,
               showanswer=None,
               rerandomize=None,
               force_save_button=None,
               attempts=None,
               problem_state=None,
               correct=False,
               done=None,
               text_customization=None
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
        location = Location(["i4x", "edX", "capa_test", "problem",
                             "SampleProblem{0}".format(cls.next_num())])
        field_data = {'data': cls.sample_problem_xml}

        if graceperiod is not None:
            field_data['graceperiod'] = graceperiod
        if due is not None:
            field_data['due'] = due
        if max_attempts is not None:
            field_data['max_attempts'] = max_attempts
        if showanswer is not None:
            field_data['showanswer'] = showanswer
        if force_save_button is not None:
            field_data['force_save_button'] = force_save_button
        if rerandomize is not None:
            field_data['rerandomize'] = rerandomize
        if done is not None:
            field_data['done'] = done
        if text_customization is not None:
            field_data['text_customization'] = text_customization

        descriptor = Mock(weight="1")
        if problem_state is not None:
            field_data.update(problem_state)
        if attempts is not None:
            # converting to int here because I keep putting "0" and "1" in the tests
            # since everything else is a string.
            field_data['attempts'] = int(attempts)

        system = get_test_system()
        system.render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaModule(
            descriptor,
            system,
            DictFieldData(field_data),
            ScopeIds(None, None, location, location),
        )

        if correct:
            # TODO: probably better to actually set the internal state properly, but...
            module.get_score = lambda: {'score': 1, 'total': 1}
        else:
            module.get_score = lambda: {'score': 0, 'total': 1}

        return module


class CapaModuleTest(unittest.TestCase):

    def setUp(self):
        now = datetime.datetime.now(UTC)
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

    def test_closed(self):

        # Attempts < Max attempts --> NOT closed
        module = CapaFactory.create(max_attempts="1", attempts="0")
        self.assertFalse(module.closed())

        # Attempts < Max attempts --> NOT closed
        module = CapaFactory.create(max_attempts="2", attempts="1")
        self.assertFalse(module.closed())

        # Attempts = Max attempts --> closed
        module = CapaFactory.create(max_attempts="1", attempts="1")
        self.assertTrue(module.closed())

        # Attempts > Max attempts --> closed
        module = CapaFactory.create(max_attempts="1", attempts="2")
        self.assertTrue(module.closed())

        # Max attempts = 0 --> closed
        module = CapaFactory.create(max_attempts="0", attempts="2")
        self.assertTrue(module.closed())

        # Past due --> closed
        module = CapaFactory.create(max_attempts="1", attempts="0",
                                    due=self.yesterday_str)
        self.assertTrue(module.closed())

    def test_parse_get_params(self):

        # Valid GET param dict
        # 'input_5' intentionally left unset,
        valid_get_dict = MultiDict({
            'input_1': 'test',
            'input_1_2': 'test',
            'input_1_2_3': 'test',
            'input_[]_3': 'test',
            'input_4': None,
            'input_6': 5
        })

        result = CapaModule.make_dict_of_responses(valid_get_dict)

        # Expect that we get a dict with "input" stripped from key names
        # and that we get the same values back
        for key in result.keys():
            original_key = "input_" + key
            self.assertTrue(original_key in valid_get_dict,
                            "Output dict should have key %s" % original_key)
            self.assertEqual(valid_get_dict[original_key], result[key])

        # Valid GET param dict with list keys
        # Each tuple represents a single parameter in the query string
        valid_get_dict = MultiDict((('input_2[]', 'test1'), ('input_2[]', 'test2')))
        result = CapaModule.make_dict_of_responses(valid_get_dict)
        self.assertTrue('2' in result)
        self.assertEqual(['test1', 'test2'], result['2'])

        # If we use [] at the end of a key name, we should always
        # get a list, even if there's just one value
        valid_get_dict = MultiDict({'input_1[]': 'test'})
        result = CapaModule.make_dict_of_responses(valid_get_dict)
        self.assertEqual(result['1'], ['test'])

        # If we have no underscores in the name, then the key is invalid
        invalid_get_dict = MultiDict({'input': 'test'})
        with self.assertRaises(ValueError):
            result = CapaModule.make_dict_of_responses(invalid_get_dict)

        # Two equivalent names (one list, one non-list)
        # One of the values would overwrite the other, so detect this
        # and raise an exception
        invalid_get_dict = MultiDict({'input_1[]': 'test 1',
                                      'input_1': 'test 2'})
        with self.assertRaises(ValueError):
            result = CapaModule.make_dict_of_responses(invalid_get_dict)

    def test_check_problem_correct(self):

        module = CapaFactory.create(attempts=1)

        # Simulate that all answers are marked correct, no matter
        # what the input is, by patching CorrectMap.is_correct()
        # Also simulate rendering the HTML
        # TODO: pep8 thinks the following line has invalid syntax
        with patch('capa.correctmap.CorrectMap.is_correct') as mock_is_correct, \
                patch('xmodule.capa_module.CapaModule.get_problem_html') as mock_html:
            mock_is_correct.return_value = True
            mock_html.return_value = "Test HTML"

            # Check the problem
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.check_problem(get_request_dict)

        # Expect that the problem is marked correct
        self.assertEqual(result['success'], 'correct')

        # Expect that we get the (mocked) HTML
        self.assertEqual(result['contents'], 'Test HTML')

        # Expect that the number of attempts is incremented by 1
        self.assertEqual(module.attempts, 2)

    def test_check_problem_incorrect(self):

        module = CapaFactory.create(attempts=0)

        # Simulate marking the input incorrect
        with patch('capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = False

            # Check the problem
            get_request_dict = {CapaFactory.input_key(): '0'}
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
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                module.check_problem(get_request_dict)

        # Expect that number of attempts NOT incremented
        self.assertEqual(module.attempts, 3)

    def test_check_problem_resubmitted_with_randomize(self):
        rerandomize_values = ['always', 'true']

        for rerandomize in rerandomize_values:
            # Randomize turned on
            module = CapaFactory.create(rerandomize=rerandomize, attempts=0)

            # Simulate that the problem is completed
            module.done = True

            # Expect that we cannot submit
            with self.assertRaises(xmodule.exceptions.NotFoundError):
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                module.check_problem(get_request_dict)

            # Expect that number of attempts NOT incremented
            self.assertEqual(module.attempts, 0)

    def test_check_problem_resubmitted_no_randomize(self):
        rerandomize_values = ['never', 'false', 'per_student']

        for rerandomize in rerandomize_values:
            # Randomize turned off
            module = CapaFactory.create(rerandomize=rerandomize, attempts=0, done=True)

            # Expect that we can submit successfully
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.check_problem(get_request_dict)

            self.assertEqual(result['success'], 'correct')

            # Expect that number of attempts IS incremented
            self.assertEqual(module.attempts, 1)

    def test_check_problem_queued(self):
        module = CapaFactory.create(attempts=1)

        # Simulate that the problem is queued
        with patch('capa.capa_problem.LoncapaProblem.is_queued') \
                as mock_is_queued, \
            patch('capa.capa_problem.LoncapaProblem.get_recentmost_queuetime') \
                as mock_get_queuetime:

            mock_is_queued.return_value = True
            mock_get_queuetime.return_value = datetime.datetime.now(UTC)

            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            self.assertTrue('You must wait' in result['success'])

        # Expect that the number of attempts is NOT incremented
        self.assertEqual(module.attempts, 1)

    def test_check_problem_error(self):

        # Try each exception that capa_module should handle
        exception_classes = [StudentInputError,
                             LoncapaProblemError,
                             ResponseError]
        for exception_class in exception_classes:

            # Create the module
            module = CapaFactory.create(attempts=1)

            # Ensure that the user is NOT staff
            module.system.user_is_staff = False

            # Simulate answering a problem that raises the exception
            with patch('capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class('test error')

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            expected_msg = 'Error: test error'
            self.assertEqual(expected_msg, result['success'])

            # Expect that the number of attempts is NOT incremented
            self.assertEqual(module.attempts, 1)

    def test_check_problem_other_errors(self):
        """
        Test that errors other than the expected kinds give an appropriate message.

        See also `test_check_problem_error` for the "expected kinds" or errors.
        """
        # Create the module
        module = CapaFactory.create(attempts=1)

        # Ensure that the user is NOT staff
        module.system.user_is_staff = False

        # Ensure that DEBUG is on
        module.system.DEBUG = True

        # Simulate answering a problem that raises the exception
        with patch('capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
            error_msg = u"Superterrible error happened: ☠"
            mock_grade.side_effect = Exception(error_msg)

            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.check_problem(get_request_dict)

        # Expect an AJAX alert message in 'success'
        self.assertTrue(error_msg in result['success'])

    def test_check_problem_error_nonascii(self):

        # Try each exception that capa_module should handle
        exception_classes = [StudentInputError,
                             LoncapaProblemError,
                             ResponseError]
        for exception_class in exception_classes:

            # Create the module
            module = CapaFactory.create(attempts=1)

            # Ensure that the user is NOT staff
            module.system.user_is_staff = False

            # Simulate answering a problem that raises the exception
            with patch('capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class(u"ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ")

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            expected_msg = u'Error: ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ'
            self.assertEqual(expected_msg, result['success'])

            # Expect that the number of attempts is NOT incremented
            self.assertEqual(module.attempts, 1)

    def test_check_problem_error_with_staff_user(self):

        # Try each exception that capa module should handle
        for exception_class in [StudentInputError,
                                LoncapaProblemError,
                                ResponseError]:

            # Create the module
            module = CapaFactory.create(attempts=1)

            # Ensure that the user IS staff
            module.system.user_is_staff = True

            # Simulate answering a problem that raises an exception
            with patch('capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class('test error')

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.check_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            self.assertTrue('test error' in result['success'])

            # We DO include traceback information for staff users
            self.assertTrue('Traceback' in result['success'])

            # Expect that the number of attempts is NOT incremented
            self.assertEqual(module.attempts, 1)

    def test_reset_problem(self):
        module = CapaFactory.create(done=True)
        module.new_lcp = Mock(wraps=module.new_lcp)
        module.choose_new_seed = Mock(wraps=module.choose_new_seed)

        # Stub out HTML rendering
        with patch('xmodule.capa_module.CapaModule.get_problem_html') as mock_html:
            mock_html.return_value = "<div>Test HTML</div>"

            # Reset the problem
            get_request_dict = {}
            result = module.reset_problem(get_request_dict)

        # Expect that the request was successful
        self.assertTrue('success' in result and result['success'])

        # Expect that the problem HTML is retrieved
        self.assertTrue('html' in result)
        self.assertEqual(result['html'], "<div>Test HTML</div>")

        # Expect that the problem was reset
        module.new_lcp.assert_called_once_with(None)

    def test_reset_problem_closed(self):
        # pre studio default
        module = CapaFactory.create(rerandomize="always")

        # Simulate that the problem is closed
        with patch('xmodule.capa_module.CapaModule.closed') as mock_closed:
            mock_closed.return_value = True

            # Try to reset the problem
            get_request_dict = {}
            result = module.reset_problem(get_request_dict)

        # Expect that the problem was NOT reset
        self.assertTrue('success' in result and not result['success'])

    def test_reset_problem_not_done(self):
        # Simulate that the problem is NOT done
        module = CapaFactory.create(done=False)

        # Try to reset the problem
        get_request_dict = {}
        result = module.reset_problem(get_request_dict)

        # Expect that the problem was NOT reset
        self.assertTrue('success' in result and not result['success'])

    def test_rescore_problem_correct(self):

        module = CapaFactory.create(attempts=1, done=True)

        # Simulate that all answers are marked correct, no matter
        # what the input is, by patching LoncapaResponse.evaluate_answers()
        with patch('capa.responsetypes.LoncapaResponse.evaluate_answers') as mock_evaluate_answers:
            mock_evaluate_answers.return_value = CorrectMap(CapaFactory.answer_key(), 'correct')
            result = module.rescore_problem()

        # Expect that the problem is marked correct
        self.assertEqual(result['success'], 'correct')

        # Expect that we get no HTML
        self.assertFalse('contents' in result)

        # Expect that the number of attempts is not incremented
        self.assertEqual(module.attempts, 1)

    def test_rescore_problem_incorrect(self):
        # make sure it also works when attempts have been reset,
        # so add this to the test:
        module = CapaFactory.create(attempts=0, done=True)

        # Simulate that all answers are marked incorrect, no matter
        # what the input is, by patching LoncapaResponse.evaluate_answers()
        with patch('capa.responsetypes.LoncapaResponse.evaluate_answers') as mock_evaluate_answers:
            mock_evaluate_answers.return_value = CorrectMap(CapaFactory.answer_key(), 'incorrect')
            result = module.rescore_problem()

        # Expect that the problem is marked incorrect
        self.assertEqual(result['success'], 'incorrect')

        # Expect that the number of attempts is not incremented
        self.assertEqual(module.attempts, 0)

    def test_rescore_problem_not_done(self):
        # Simulate that the problem is NOT done
        module = CapaFactory.create(done=False)

        # Try to rescore the problem, and get exception
        with self.assertRaises(xmodule.exceptions.NotFoundError):
            module.rescore_problem()

    def test_rescore_problem_not_supported(self):
        module = CapaFactory.create(done=True)

        # Try to rescore the problem, and get exception
        with patch('capa.capa_problem.LoncapaProblem.supports_rescoring') as mock_supports_rescoring:
            mock_supports_rescoring.return_value = False
            with self.assertRaises(NotImplementedError):
                module.rescore_problem()

    def _rescore_problem_error_helper(self, exception_class):
        """Helper to allow testing all errors that rescoring might return."""
        # Create the module
        module = CapaFactory.create(attempts=1, done=True)

        # Simulate answering a problem that raises the exception
        with patch('capa.capa_problem.LoncapaProblem.rescore_existing_answers') as mock_rescore:
            mock_rescore.side_effect = exception_class(u'test error \u03a9')
            result = module.rescore_problem()

        # Expect an AJAX alert message in 'success'
        expected_msg = u'Error: test error \u03a9'
        self.assertEqual(result['success'], expected_msg)

        # Expect that the number of attempts is NOT incremented
        self.assertEqual(module.attempts, 1)

    def test_rescore_problem_student_input_error(self):
        self._rescore_problem_error_helper(StudentInputError)

    def test_rescore_problem_problem_error(self):
        self._rescore_problem_error_helper(LoncapaProblemError)

    def test_rescore_problem_response_error(self):
        self._rescore_problem_error_helper(ResponseError)

    def test_save_problem(self):
        module = CapaFactory.create(done=False)

        # Save the problem
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        result = module.save_problem(get_request_dict)

        # Expect that answers are saved to the problem
        expected_answers = {CapaFactory.answer_key(): '3.14'}
        self.assertEqual(module.lcp.student_answers, expected_answers)

        # Expect that the result is success
        self.assertTrue('success' in result and result['success'])

    def test_save_problem_closed(self):
        module = CapaFactory.create(done=False)

        # Simulate that the problem is closed
        with patch('xmodule.capa_module.CapaModule.closed') as mock_closed:
            mock_closed.return_value = True

            # Try to save the problem
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.save_problem(get_request_dict)

        # Expect that the result is failure
        self.assertTrue('success' in result and not result['success'])

    def test_save_problem_submitted_with_randomize(self):

        # Capa XModule treats 'always' and 'true' equivalently
        rerandomize_values = ['always', 'true']

        for rerandomize in rerandomize_values:
            module = CapaFactory.create(rerandomize=rerandomize, done=True)

            # Try to save
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.save_problem(get_request_dict)

            # Expect that we cannot save
            self.assertTrue('success' in result and not result['success'])

    def test_save_problem_submitted_no_randomize(self):

        # Capa XModule treats 'false' and 'per_student' equivalently
        rerandomize_values = ['never', 'false', 'per_student']

        for rerandomize in rerandomize_values:
            module = CapaFactory.create(rerandomize=rerandomize, done=True)

            # Try to save
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.save_problem(get_request_dict)

            # Expect that we succeed
            self.assertTrue('success' in result and result['success'])

    def test_check_button_name(self):

        # If last attempt, button name changes to "Final Check"
        # Just in case, we also check what happens if we have
        # more attempts than allowed.
        attempts = random.randint(1, 10)
        module = CapaFactory.create(attempts=attempts - 1, max_attempts=attempts)
        self.assertEqual(module.check_button_name(), "Final Check")

        module = CapaFactory.create(attempts=attempts, max_attempts=attempts)
        self.assertEqual(module.check_button_name(), "Final Check")

        module = CapaFactory.create(attempts=attempts + 1, max_attempts=attempts)
        self.assertEqual(module.check_button_name(), "Final Check")

        # Otherwise, button name is "Check"
        module = CapaFactory.create(attempts=attempts - 2, max_attempts=attempts)
        self.assertEqual(module.check_button_name(), "Check")

        module = CapaFactory.create(attempts=attempts - 3, max_attempts=attempts)
        self.assertEqual(module.check_button_name(), "Check")

        # If no limit on attempts, then always show "Check"
        module = CapaFactory.create(attempts=attempts - 3)
        self.assertEqual(module.check_button_name(), "Check")

        module = CapaFactory.create(attempts=0)
        self.assertEqual(module.check_button_name(), "Check")

    def test_check_button_name_customization(self):
        module = CapaFactory.create(attempts=1,
                                    max_attempts=10,
                                    text_customization={"custom_check": "Submit", "custom_final_check": "Final Submit"}
                                    )
        self.assertEqual(module.check_button_name(), "Submit")

        module = CapaFactory.create(attempts=9,
                                    max_attempts=10,
                                    text_customization={"custom_check": "Submit", "custom_final_check": "Final Submit"}
                                    )
        self.assertEqual(module.check_button_name(), "Final Submit")

    def test_should_show_check_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, do NOT show check button
        module = CapaFactory.create(due=self.yesterday_str)
        self.assertFalse(module.should_show_check_button())

        # If user is out of attempts, do NOT show the check button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts)
        self.assertFalse(module.should_show_check_button())

        # If survey question (max_attempts = 0), do NOT show the check button
        module = CapaFactory.create(max_attempts=0)
        self.assertFalse(module.should_show_check_button())

        # If user submitted a problem but hasn't reset,
        # do NOT show the check button
        # Note:  we can only reset when rerandomize="always" or "true"
        module = CapaFactory.create(rerandomize="always", done=True)
        self.assertFalse(module.should_show_check_button())

        module = CapaFactory.create(rerandomize="true", done=True)
        self.assertFalse(module.should_show_check_button())

        # Otherwise, DO show the check button
        module = CapaFactory.create()
        self.assertTrue(module.should_show_check_button())

        # If the user has submitted the problem
        # and we do NOT have a reset button, then we can show the check button
        # Setting rerandomize to "never" or "false" ensures that the reset button
        # is not shown
        module = CapaFactory.create(rerandomize="never", done=True)
        self.assertTrue(module.should_show_check_button())

        module = CapaFactory.create(rerandomize="false", done=True)
        self.assertTrue(module.should_show_check_button())

        module = CapaFactory.create(rerandomize="per_student", done=True)
        self.assertTrue(module.should_show_check_button())

    def test_should_show_reset_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, do NOT show the reset button
        module = CapaFactory.create(due=self.yesterday_str, done=True)
        self.assertFalse(module.should_show_reset_button())

        # If the user is out of attempts, do NOT show the reset button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts, done=True)
        self.assertFalse(module.should_show_reset_button())

        # If we're NOT randomizing, then do NOT show the reset button
        module = CapaFactory.create(rerandomize="never", done=True)
        self.assertFalse(module.should_show_reset_button())

        # If we're NOT randomizing, then do NOT show the reset button
        module = CapaFactory.create(rerandomize="per_student", done=True)
        self.assertFalse(module.should_show_reset_button())

        # If we're NOT randomizing, then do NOT show the reset button
        module = CapaFactory.create(rerandomize="false", done=True)
        self.assertFalse(module.should_show_reset_button())

        # If the user hasn't submitted an answer yet,
        # then do NOT show the reset button
        module = CapaFactory.create(done=False)
        self.assertFalse(module.should_show_reset_button())

        # pre studio default value, DO show the reset button
        module = CapaFactory.create(rerandomize="always", done=True)
        self.assertTrue(module.should_show_reset_button())

        # If survey question for capa (max_attempts = 0),
        # DO show the reset button
        module = CapaFactory.create(rerandomize="always", max_attempts=0, done=True)
        self.assertTrue(module.should_show_reset_button())

    def test_should_show_save_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, do NOT show the save button
        module = CapaFactory.create(due=self.yesterday_str, done=True)
        self.assertFalse(module.should_show_save_button())

        # If the user is out of attempts, do NOT show the save button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts, done=True)
        self.assertFalse(module.should_show_save_button())

        # If user submitted a problem but hasn't reset, do NOT show the save button
        module = CapaFactory.create(rerandomize="always", done=True)
        self.assertFalse(module.should_show_save_button())

        module = CapaFactory.create(rerandomize="true", done=True)
        self.assertFalse(module.should_show_save_button())

        # If the user has unlimited attempts and we are not randomizing,
        # then do NOT show a save button
        # because they can keep using "Check"
        module = CapaFactory.create(max_attempts=None, rerandomize="never", done=False)
        self.assertFalse(module.should_show_save_button())

        module = CapaFactory.create(max_attempts=None, rerandomize="false", done=True)
        self.assertFalse(module.should_show_save_button())

        module = CapaFactory.create(max_attempts=None, rerandomize="per_student", done=True)
        self.assertFalse(module.should_show_save_button())

        # pre-studio default, DO show the save button
        module = CapaFactory.create(rerandomize="always", done=False)
        self.assertTrue(module.should_show_save_button())

        # If we're not randomizing and we have limited attempts,  then we can save
        module = CapaFactory.create(rerandomize="never", max_attempts=2, done=True)
        self.assertTrue(module.should_show_save_button())

        module = CapaFactory.create(rerandomize="false", max_attempts=2, done=True)
        self.assertTrue(module.should_show_save_button())

        module = CapaFactory.create(rerandomize="per_student", max_attempts=2, done=True)
        self.assertTrue(module.should_show_save_button())

        # If survey question for capa (max_attempts = 0),
        # DO show the save button
        module = CapaFactory.create(max_attempts=0, done=False)
        self.assertTrue(module.should_show_save_button())

    def test_should_show_save_button_force_save_button(self):
        # If we're after the deadline, do NOT show the save button
        # even though we're forcing a save
        module = CapaFactory.create(due=self.yesterday_str,
                                    force_save_button="true",
                                    done=True)
        self.assertFalse(module.should_show_save_button())

        # If the user is out of attempts, do NOT show the save button
        attempts = random.randint(1, 10)
        module = CapaFactory.create(attempts=attempts,
                                    max_attempts=attempts,
                                    force_save_button="true",
                                    done=True)
        self.assertFalse(module.should_show_save_button())

        # Otherwise, if we force the save button,
        # then show it even if we would ordinarily
        # require a reset first
        module = CapaFactory.create(force_save_button="true",
                                    rerandomize="always",
                                    done=True)
        self.assertTrue(module.should_show_save_button())

        module = CapaFactory.create(force_save_button="true",
                                    rerandomize="true",
                                    done=True)
        self.assertTrue(module.should_show_save_button())

    def test_no_max_attempts(self):
        module = CapaFactory.create(max_attempts='')
        html = module.get_problem_html()
        self.assertTrue(html is not None)
        # assert that we got here without exploding

    def test_get_problem_html(self):
        module = CapaFactory.create()

        # We've tested the show/hide button logic in other tests,
        # so here we hard-wire the values
        show_check_button = bool(random.randint(0, 1) % 2)
        show_reset_button = bool(random.randint(0, 1) % 2)
        show_save_button = bool(random.randint(0, 1) % 2)

        module.should_show_check_button = Mock(return_value=show_check_button)
        module.should_show_reset_button = Mock(return_value=show_reset_button)
        module.should_show_save_button = Mock(return_value=show_save_button)

        # Mock the system rendering function
        module.system.render_template = Mock(return_value="<div>Test Template HTML</div>")

        # Patch the capa problem's HTML rendering
        with patch('capa.capa_problem.LoncapaProblem.get_html') as mock_html:
            mock_html.return_value = "<div>Test Problem HTML</div>"

            # Render the problem HTML
            html = module.get_problem_html(encapsulate=False)

            # Also render the problem encapsulated in a <div>
            html_encapsulated = module.get_problem_html(encapsulate=True)

        # Expect that we get the rendered template back
        self.assertEqual(html, "<div>Test Template HTML</div>")

        # Check the rendering context
        render_args, _ = module.system.render_template.call_args
        self.assertEqual(len(render_args), 2)

        template_name = render_args[0]
        self.assertEqual(template_name, "problem.html")

        context = render_args[1]
        self.assertEqual(context['problem']['html'], "<div>Test Problem HTML</div>")
        self.assertEqual(bool(context['check_button']), show_check_button)
        self.assertEqual(bool(context['reset_button']), show_reset_button)
        self.assertEqual(bool(context['save_button']), show_save_button)

        # Assert that the encapsulated html contains the original html
        self.assertTrue(html in html_encapsulated)

    def test_input_state_consistency(self):
        module1 = CapaFactory.create()
        module2 = CapaFactory.create()

        # check to make sure that the input_state and the keys have the same values
        module1.set_state_from_lcp()
        self.assertEqual(module1.lcp.inputs.keys(), module1.input_state.keys())

        module2.set_state_from_lcp()

        intersection = set(module2.input_state.keys()).intersection(set(module1.input_state.keys()))
        self.assertEqual(len(intersection), 0)

    def test_get_problem_html_error(self):
        """
        In production, when an error occurs with the problem HTML
        rendering, a "dummy" problem is created with an error
        message to display to the user.
        """
        module = CapaFactory.create()

        # Save the original problem so we can compare it later
        original_problem = module.lcp

        # Simulate throwing an exception when the capa problem
        # is asked to render itself as HTML
        module.lcp.get_html = Mock(side_effect=Exception("Test"))

        # Stub out the get_test_system rendering function
        module.system.render_template = Mock(return_value="<div>Test Template HTML</div>")

        # Turn off DEBUG
        module.system.DEBUG = False

        # Try to render the module with DEBUG turned off
        html = module.get_problem_html()

        self.assertTrue(html is not None)

        # Check the rendering context
        render_args, _ = module.system.render_template.call_args
        context = render_args[1]
        self.assertTrue("error" in context['problem']['html'])

        # Expect that the module has created a new dummy problem with the error
        self.assertNotEqual(original_problem, module.lcp)

    def test_get_problem_html_error_w_debug(self):
        """
        Test the html response when an error occurs with DEBUG on
        """
        module = CapaFactory.create()

        # Simulate throwing an exception when the capa problem
        # is asked to render itself as HTML
        error_msg = u"Superterrible error happened: ☠"
        module.lcp.get_html = Mock(side_effect=Exception(error_msg))

        # Stub out the get_test_system rendering function
        module.system.render_template = Mock(return_value="<div>Test Template HTML</div>")

        # Make sure DEBUG is on
        module.system.DEBUG = True

        # Try to render the module with DEBUG turned on
        html = module.get_problem_html()

        self.assertTrue(html is not None)

        # Check the rendering context
        render_args, _ = module.system.render_template.call_args
        context = render_args[1]
        self.assertTrue(error_msg in context['problem']['html'])

    def test_random_seed_no_change(self):

        # Run the test for each possible rerandomize value
        for rerandomize in ['false', 'never',
                            'per_student', 'always',
                            'true', 'onreset']:
            module = CapaFactory.create(rerandomize=rerandomize)

            # Get the seed
            # By this point, the module should have persisted the seed
            seed = module.seed
            self.assertTrue(seed is not None)

            # If we're not rerandomizing, the seed is always set
            # to the same value (1)
            if rerandomize in ['never']:
                self.assertEqual(seed, 1,
                                 msg="Seed should always be 1 when rerandomize='%s'" % rerandomize)

            # Check the problem
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            module.check_problem(get_request_dict)

            # Expect that the seed is the same
            self.assertEqual(seed, module.seed)

            # Save the problem
            module.save_problem(get_request_dict)

            # Expect that the seed is the same
            self.assertEqual(seed, module.seed)

    def test_random_seed_with_reset(self):

        def _reset_and_get_seed(module):
            '''
            Reset the XModule and return the module's seed
            '''

            # Simulate submitting an attempt
            # We need to do this, or reset_problem() will
            # fail with a complaint that we haven't submitted
            # the problem yet.
            module.done = True

            # Reset the problem
            module.reset_problem({})

            # Return the seed
            return module.seed

        def _retry_and_check(num_tries, test_func):
            '''
            Returns True if *test_func* was successful
            (returned True) within *num_tries* attempts

            *test_func* must be a function
            of the form test_func() -> bool
            '''
            success = False
            for i in range(num_tries):
                if test_func() is True:
                    success = True
                    break
            return success

        # Run the test for each possible rerandomize value
        for rerandomize in ['never', 'false', 'per_student',
                            'always', 'true', 'onreset']:
            module = CapaFactory.create(rerandomize=rerandomize)

            # Get the seed
            # By this point, the module should have persisted the seed
            seed = module.seed
            self.assertTrue(seed is not None)

            # We do NOT want the seed to reset if rerandomize
            # is set to 'never' -- it should still be 1
            # The seed also stays the same if we're randomizing
            # 'per_student': the same student should see the same problem
            if rerandomize in ['never', 'false', 'per_student']:
                self.assertEqual(seed, _reset_and_get_seed(module))

            # Otherwise, we expect the seed to change
            # to another valid seed
            else:

                # Since there's a small chance we might get the
                # same seed again, give it 5 chances
                # to generate a different seed
                success = _retry_and_check(5, lambda: _reset_and_get_seed(module) != seed)

                self.assertTrue(module.seed is not None)
                msg = 'Could not get a new seed from reset after 5 tries'
                self.assertTrue(success, msg)

    def test_random_seed_bins(self):
        # Assert that we are limiting the number of possible seeds.

        # Check the conditions that generate random seeds
        for rerandomize in ['always', 'per_student', 'true', 'onreset']:
            # Get a bunch of seeds, they should all be in 0-999.
            for i in range(200):
                module = CapaFactory.create(rerandomize=rerandomize)
                assert 0 <= module.seed < 1000

    @patch('xmodule.capa_module.log')
    @patch('xmodule.capa_module.Progress')
    def test_get_progress_error(self, mock_progress, mock_log):
        """
        Check that an exception given in `Progress` produces a `log.exception` call.
        """
        error_types = [TypeError, ValueError]
        for error_type in error_types:
            mock_progress.side_effect = error_type
            module = CapaFactory.create()
            self.assertIsNone(module.get_progress())
            mock_log.exception.assert_called_once_with('Got bad progress')
            mock_log.reset_mock()

    @patch('xmodule.capa_module.Progress')
    def test_get_progress_calculate_progress_fraction(self, mock_progress):
        """
        Check that score and total are calculated correctly for the progress fraction.
        """
        module = CapaFactory.create()
        module.weight = 1
        module.get_progress()
        mock_progress.assert_called_with(0, 1)

        other_module = CapaFactory.create(correct=True)
        other_module.weight = 1
        other_module.get_progress()
        mock_progress.assert_called_with(1, 1)

    def test_get_html(self):
        """
        Check that get_html() calls get_progress() with no arguments.
        """
        module = CapaFactory.create()
        module.get_progress = Mock(wraps=module.get_progress)
        module.get_html()
        module.get_progress.assert_called_once_with()

    def test_get_problem(self):
        """
        Check that get_problem() returns the expected dictionary.
        """
        module = CapaFactory.create()
        self.assertEquals(module.get_problem("data"), {'html': module.get_problem_html(encapsulate=False)})


class ComplexEncoderTest(unittest.TestCase):
    def test_default(self):
        """
        Check that complex numbers can be encoded into JSON.
        """
        complex_num = 1 - 1j
        expected_str = '1-1*j'
        json_str = json.dumps(complex_num, cls=ComplexEncoder)
        self.assertEqual(expected_str, json_str[1:-1])  # ignore quotes
