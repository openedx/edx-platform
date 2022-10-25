"""
Tests of the Capa XModule
"""
# pylint: disable=invalid-name


import datetime
import json
import os
import random
import textwrap
import unittest
from unittest.mock import DEFAULT, Mock, patch

import pytest
import ddt
import requests
import webob
from codejail.safe_exec import SafeExecException
from django.test import override_settings
from django.utils.encoding import smart_str
from edx_user_state_client.interface import XBlockUserState
from lxml import etree
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from pytz import UTC
from webob.multidict import MultiDict
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.scorable import Score

import xmodule
from xmodule.capa import responsetypes
from xmodule.capa.correctmap import CorrectMap
from xmodule.capa.responsetypes import LoncapaProblemError, ResponseError, StudentInputError
from xmodule.capa.xqueue_interface import XQueueInterface
from xmodule.capa_module import ComplexEncoder, ProblemBlock
from xmodule.tests import DATA_DIR

from ..capa_module import RANDOMIZATION, SHOWANSWER
from . import get_test_system


class CapaFactory:
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
    def input_key(cls, response_num=2, input_num=1):
        """
        Return the input key to use when passing GET parameters
        """
        return "input_" + cls.answer_key(response_num, input_num)

    @classmethod
    def answer_key(cls, response_num=2, input_num=1):
        """
        Return the key stored in the capa problem answer dict
        """
        return ("%s_%d_%d" % ("-".join(['i4x', 'edX', 'capa_test', 'problem', 'SampleProblem%d' % cls.num]),
                              response_num, input_num))

    @classmethod
    def create(cls, attempts=None, problem_state=None, correct=False, xml=None, override_get_score=True,
               render_template=None, **kwargs):
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

            render_template: pass function or Mock for testing
        """
        location = BlockUsageLocator(
            CourseLocator("edX", "capa_test", "2012_Fall", deprecated=True),
            "problem",
            f"SampleProblem{cls.next_num()}",
            deprecated=True,
        )
        if xml is None:
            xml = cls.sample_problem_xml
        field_data = {'data': xml}
        field_data.update(kwargs)
        if problem_state is not None:
            field_data.update(problem_state)
        if attempts is not None:
            # converting to int here because I keep putting "0" and "1" in the tests
            # since everything else is a string.
            field_data['attempts'] = int(attempts)

        system = get_test_system(
            course_id=location.course_key,
            user_is_staff=kwargs.get('user_is_staff', False),
            render_template=render_template or Mock(return_value="<div>Test Template HTML</div>"),
        )
        module = ProblemBlock(
            system,
            DictFieldData(field_data),
            ScopeIds(None, 'problem', location, location),
        )
        assert module.lcp

        if override_get_score:
            if correct:
                # TODO: probably better to actually set the internal state properly, but...
                module.score = Score(raw_earned=1, raw_possible=1)
            else:
                module.score = Score(raw_earned=0, raw_possible=1)

        module.graded = 'False'
        module.weight = 1
        return module


class CapaFactoryWithFiles(CapaFactory):
    """
    A factory for creating a Capa problem with files attached.
    """
    sample_problem_xml = textwrap.dedent("""\
        <problem>
            <coderesponse queuename="BerkeleyX-cs188x">
                <!-- actual filenames here don't matter for server-side tests,
                     they are only acted upon in the browser. -->
                <filesubmission
                    points="25"
                    allowed_files="prog1.py prog2.py prog3.py"
                    required_files="prog1.py prog2.py prog3.py"
                />
                <codeparam>
                    <answer_display>
                        If you're having trouble with this Project,
                        please refer to the Lecture Slides and attend office hours.
                    </answer_display>
                    <grader_payload>{"project": "p3"}</grader_payload>
                </codeparam>
            </coderesponse>

            <customresponse>
                <text>
                    If you worked with a partner, enter their username or email address. If you
                    worked alone, enter None.
                </text>

                <textline points="0" size="40" correct_answer="Your partner's username or 'None'"/>
                <answer type="loncapa/python">
correct=['correct']
s = str(submission[0]).strip()
if submission[0] == '':
    correct[0] = 'incorrect'
                </answer>
            </customresponse>
        </problem>
    """)


@ddt.ddt
class ProblemBlockTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def setUp(self):
        super().setUp()

        now = datetime.datetime.now(UTC)
        day_delta = datetime.timedelta(days=1)
        self.yesterday_str = str(now - day_delta)
        self.today_str = str(now)
        self.tomorrow_str = str(now + day_delta)

        # in the capa grace period format, not in time delta format
        self.two_day_delta_str = "2 days"

    def test_import(self):
        module = CapaFactory.create()
        assert module.get_score().raw_earned == 0

        other_module = CapaFactory.create()
        assert module.get_score().raw_earned == 0
        assert module.url_name != other_module.url_name, 'Factory should be creating unique names for each problem'

    def test_correct(self):
        """
        Check that the factory creates correct and incorrect problems properly.
        """
        module = CapaFactory.create()
        assert module.get_score().raw_earned == 0

        other_module = CapaFactory.create(correct=True)
        assert other_module.get_score().raw_earned == 1

    def test_get_score(self):
        """
        Tests the internals of get_score. In keeping with the ScorableXBlock spec,
        Capa modules store their score independently of the LCP internals, so it must
        be explicitly updated.
        """
        student_answers = {'1_2_1': 'abcd'}
        correct_map = CorrectMap(answer_id='1_2_1', correctness="correct", npoints=0.9)
        module = CapaFactory.create(correct=True, override_get_score=False)
        module.lcp.correct_map = correct_map
        module.lcp.student_answers = student_answers
        assert module.get_score().raw_earned == 0.0
        module.set_score(module.score_from_lcp(module.lcp))
        assert module.get_score().raw_earned == 0.9

        other_correct_map = CorrectMap(answer_id='1_2_1', correctness="incorrect", npoints=0.1)
        other_module = CapaFactory.create(correct=False, override_get_score=False)
        other_module.lcp.correct_map = other_correct_map
        other_module.lcp.student_answers = student_answers
        assert other_module.get_score().raw_earned == 0.0
        other_module.set_score(other_module.score_from_lcp(other_module.lcp))
        assert other_module.get_score().raw_earned == 0.1

    def test_showanswer_default(self):
        """
        Make sure the show answer logic does the right thing.
        """
        # default, no due date, showanswer 'closed', so problem is open, and show_answer
        # not visible.
        problem = CapaFactory.create()
        assert not problem.answer_available()

    @ddt.data(
        (requests.exceptions.ReadTimeout, (1, 'failed to read from the server')),
        (requests.exceptions.ConnectionError, (1, 'cannot connect to server')),
    )
    @ddt.unpack
    def test_xqueue_request_exception(self, exception, result):
        """
        Makes sure that platform will raise appropriate exception in case of
        connect/read timeout(s) to request to xqueue
        """
        xqueue_interface = XQueueInterface("http://example.com/xqueue", Mock())
        with patch.object(xqueue_interface.session, 'post', side_effect=exception):
            # pylint: disable = protected-access
            response = xqueue_interface._http_post('http://some/fake/url', {})
            assert response == result

    def test_showanswer_attempted(self):
        problem = CapaFactory.create(showanswer='attempted')
        assert not problem.answer_available()
        problem.attempts = 1
        assert problem.answer_available()

    @ddt.data(
        # If show_correctness=always, Answer is visible after attempted
        ({'showanswer': 'attempted', 'max_attempts': '1', 'show_correctness': 'always', }, False, True),
        # If show_correctness=never, Answer is never visible
        ({'showanswer': 'attempted', 'max_attempts': '1', 'show_correctness': 'never', }, False, False),
        # If show_correctness=past_due, answer is not visible before due date
        ({'showanswer': 'attempted', 'show_correctness': 'past_due', 'max_attempts': '1', 'due': 'tomorrow_str', },
         False, False),
        # If show_correctness=past_due, answer is visible after due date
        ({'showanswer': 'attempted', 'show_correctness': 'past_due', 'max_attempts': '1', 'due': 'yesterday_str', },
         True, True))
    @ddt.unpack
    def test_showanswer_hide_correctness(self, problem_data, answer_available_no_attempt,
                                         answer_available_after_attempt):
        """
        Ensure that the answer will not be shown when correctness is being hidden.
        """
        if 'due' in problem_data:
            problem_data['due'] = getattr(self, problem_data['due'])
        problem = CapaFactory.create(**problem_data)
        assert problem.answer_available() == answer_available_no_attempt
        problem.attempts = 1
        assert problem.answer_available() == answer_available_after_attempt

    def test_showanswer_closed(self):

        # can see after attempts used up, even with due date in the future
        used_all_attempts = CapaFactory.create(showanswer='closed',
                                               max_attempts="1",
                                               attempts="1",
                                               due=self.tomorrow_str)
        assert used_all_attempts.answer_available()

        # can see after due date
        after_due_date = CapaFactory.create(showanswer='closed',
                                            max_attempts="1",
                                            attempts="0",
                                            due=self.yesterday_str)

        assert after_due_date.answer_available()

        # can't see because attempts left
        attempts_left_open = CapaFactory.create(showanswer='closed',
                                                max_attempts="1",
                                                attempts="0",
                                                due=self.tomorrow_str)
        assert not attempts_left_open.answer_available()

        # Can't see because grace period hasn't expired
        still_in_grace = CapaFactory.create(showanswer='closed',
                                            max_attempts="1",
                                            attempts="0",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        assert not still_in_grace.answer_available()

    def test_showanswer_correct_or_past_due(self):
        """
        With showanswer="correct_or_past_due" should show answer after the answer is correct
        or after the problem is closed for everyone--e.g. after due date + grace period.
        """

        # can see because answer is correct, even with due date in the future
        answer_correct = CapaFactory.create(showanswer='correct_or_past_due',
                                            max_attempts="1",
                                            attempts="0",
                                            due=self.tomorrow_str,
                                            correct=True)
        assert answer_correct.answer_available()

        # can see after due date, even when answer isn't correct
        past_due_date = CapaFactory.create(showanswer='correct_or_past_due',
                                           max_attempts="1",
                                           attempts="0",
                                           due=self.yesterday_str)
        assert past_due_date.answer_available()

        # can also see after due date when answer _is_ correct
        past_due_date_correct = CapaFactory.create(showanswer='correct_or_past_due',
                                                   max_attempts="1",
                                                   attempts="0",
                                                   due=self.yesterday_str,
                                                   correct=True)
        assert past_due_date_correct.answer_available()

        # Can't see because grace period hasn't expired and answer isn't correct
        still_in_grace = CapaFactory.create(showanswer='correct_or_past_due',
                                            max_attempts="1",
                                            attempts="1",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        assert not still_in_grace.answer_available()

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
        assert not used_all_attempts.answer_available()

        # can see after due date
        past_due_date = CapaFactory.create(showanswer='past_due',
                                           max_attempts="1",
                                           attempts="0",
                                           due=self.yesterday_str)
        assert past_due_date.answer_available()

        # can't see because attempts left
        attempts_left_open = CapaFactory.create(showanswer='past_due',
                                                max_attempts="1",
                                                attempts="0",
                                                due=self.tomorrow_str)
        assert not attempts_left_open.answer_available()

        # Can't see because grace period hasn't expired, even though have no more
        # attempts.
        still_in_grace = CapaFactory.create(showanswer='past_due',
                                            max_attempts="1",
                                            attempts="1",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        assert not still_in_grace.answer_available()

    def test_showanswer_after_attempts_with_max(self):
        """
        Button should not be visible when attempts < required attempts.

        Even with max attempts set, the show answer button should only
        show up after the user has attempted answering the question for
        the requisite number of times, i.e `attempts_before_showanswer_button`
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts='2',
            attempts_before_showanswer_button='3',
            max_attempts='5',
        )
        assert not problem.answer_available()

    def test_showanswer_after_attempts_no_max(self):
        """
        Button should not be visible when attempts < required attempts.

        Even when max attempts is NOT set, the answer should still
        only be available after the student has attempted the
        problem at least `attempts_before_showanswer_button` times
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts='2',
            attempts_before_showanswer_button='3',
        )
        assert not problem.answer_available()

    def test_showanswer_after_attempts_used_all_attempts(self):
        """
        Button should be visible even after all attempts are used up.

        As long as the student has attempted  the question for
        the requisite number of times, then the show ans. button is
        visible even after they have exhausted their attempts.
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts_before_showanswer_button='2',
            max_attempts='3',
            attempts='3',
            due=self.tomorrow_str,
        )
        assert problem.answer_available()

    def test_showanswer_after_attempts_past_due_date(self):
        """
        Show Answer button should be visible even after the due date.

        As long as the student has attempted the problem for the requisite
        number of times, the answer should be available past the due date.
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts_before_showanswer_button='2',
            attempts='2',
            due=self.yesterday_str,
        )
        assert problem.answer_available()

    def test_showanswer_after_attempts_still_in_grace(self):
        """
        If attempts > required attempts, ans. is available in grace period.

        As long as the user has attempted for the requisite # of times,
        the show answer button is visible throughout the grace period.
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            after_attempts='3',
            attempts='4',
            due=self.yesterday_str,
            graceperiod=self.two_day_delta_str,
        )
        assert problem.answer_available()

    def test_showanswer_after_attempts_large(self):
        """
        If required attempts > max attempts then required attempts = max attempts.

        Ensure that if attempts_before_showanswer_button > max_attempts,
        the button should show up after all attempts are used up,
        i.e after_attempts falls back to max_attempts
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts_before_showanswer_button='5',
            max_attempts='3',
            attempts='3',
        )
        assert problem.answer_available()

    def test_showanswer_after_attempts_zero(self):
        """
        Button should always be visible if required min attempts = 0.

        If attempts_before_showanswer_button = 0, then the show answer
        button should be visible at all times.
        """
        problem = CapaFactory.create(
            showanswer='after_attempts',
            attempts_before_showanswer_button='0',
            attempts='0',
        )
        assert problem.answer_available()

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
        assert used_all_attempts.answer_available()

        # can see after due date
        past_due_date = CapaFactory.create(showanswer='finished',
                                           max_attempts="1",
                                           attempts="0",
                                           due=self.yesterday_str)
        assert past_due_date.answer_available()

        # can't see because attempts left and wrong
        attempts_left_open = CapaFactory.create(showanswer='finished',
                                                max_attempts="1",
                                                attempts="0",
                                                due=self.tomorrow_str)
        assert not attempts_left_open.answer_available()

        # _can_ see because attempts left and right
        correct_ans = CapaFactory.create(showanswer='finished',
                                         max_attempts="1",
                                         attempts="0",
                                         due=self.tomorrow_str,
                                         correct=True)
        assert correct_ans.answer_available()

        # Can see even though grace period hasn't expired, because have no more
        # attempts.
        still_in_grace = CapaFactory.create(showanswer='finished',
                                            max_attempts="1",
                                            attempts="1",
                                            due=self.yesterday_str,
                                            graceperiod=self.two_day_delta_str)
        assert still_in_grace.answer_available()

    def test_showanswer_answered(self):
        """
        Tests that with showanswer="answered" should show answer after the problem is correctly answered.
        It should *NOT* show answer if the answer is incorrect.
        """
        # Can not see "Show Answer" when student answer is wrong
        answer_wrong = CapaFactory.create(
            showanswer=SHOWANSWER.ANSWERED,
            max_attempts="1",
            attempts="0",
            due=self.tomorrow_str,
            correct=False
        )
        assert not answer_wrong.answer_available()

        # Expect to see "Show Answer" when answer is correct
        answer_correct = CapaFactory.create(
            showanswer=SHOWANSWER.ANSWERED,
            max_attempts="1",
            attempts="0",
            due=self.tomorrow_str,
            correct=True
        )
        assert answer_correct.answer_available()

    @ddt.data('', 'other-value')
    def test_show_correctness_other(self, show_correctness):
        """
        Test that correctness is visible if show_correctness is not set to one of the values
        from SHOW_CORRECTNESS constant.
        """
        problem = CapaFactory.create(show_correctness=show_correctness)
        assert problem.correctness_available()

    def test_show_correctness_default(self):
        """
        Test that correctness is visible by default.
        """
        problem = CapaFactory.create()
        assert problem.correctness_available()

    def test_show_correctness_never(self):
        """
        Test that correctness is hidden when show_correctness turned off.
        """
        problem = CapaFactory.create(show_correctness='never')
        assert not problem.correctness_available()

    @ddt.data(
        # Correctness not visible if due date in the future, even after using up all attempts
        ({'show_correctness': 'past_due', 'max_attempts': '1', 'attempts': '1', 'due': 'tomorrow_str', }, False),
        # Correctness visible if due date in the past
        ({'show_correctness': 'past_due', 'max_attempts': '1', 'attempts': '0', 'due': 'yesterday_str', }, True),
        # Correctness not visible if due date in the future
        ({'show_correctness': 'past_due', 'max_attempts': '1', 'attempts': '0', 'due': 'tomorrow_str', }, False),
        # Correctness not visible because grace period hasn't expired,
        # even after using up all attempts
        ({'show_correctness': 'past_due', 'max_attempts': '1', 'attempts': '1', 'due': 'yesterday_str',
          'graceperiod': 'two_day_delta_str', }, False))
    @ddt.unpack
    def test_show_correctness_past_due(self, problem_data, expected_result):
        """
        Test that with show_correctness="past_due", correctness will only be visible
        after the problem is closed for everyone--e.g. after due date + grace period.
        """
        problem_data['due'] = getattr(self, problem_data['due'])
        if 'graceperiod' in problem_data:
            problem_data['graceperiod'] = getattr(self, problem_data['graceperiod'])
        problem = CapaFactory.create(**problem_data)
        assert problem.correctness_available() == expected_result

    def test_closed(self):

        # Attempts < Max attempts --> NOT closed
        module = CapaFactory.create(max_attempts="1", attempts="0")
        assert not module.closed()

        # Attempts < Max attempts --> NOT closed
        module = CapaFactory.create(max_attempts="2", attempts="1")
        assert not module.closed()

        # Attempts = Max attempts --> closed
        module = CapaFactory.create(max_attempts="1", attempts="1")
        assert module.closed()

        # Attempts > Max attempts --> closed
        module = CapaFactory.create(max_attempts="1", attempts="2")
        assert module.closed()

        # Max attempts = 0 --> closed
        module = CapaFactory.create(max_attempts="0", attempts="2")
        assert module.closed()

        # Past due --> closed
        module = CapaFactory.create(max_attempts="1", attempts="0",
                                    due=self.yesterday_str)
        assert module.closed()

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

        result = ProblemBlock.make_dict_of_responses(valid_get_dict)

        # Expect that we get a dict with "input" stripped from key names
        # and that we get the same values back
        for key in result.keys():  # lint-amnesty, pylint: disable=consider-iterating-dictionary
            original_key = "input_" + key
            assert original_key in valid_get_dict, ('Output dict should have key %s' % original_key)
            assert valid_get_dict[original_key] == result[key]

        # Valid GET param dict with list keys
        # Each tuple represents a single parameter in the query string
        valid_get_dict = MultiDict((('input_2[]', 'test1'), ('input_2[]', 'test2')))
        result = ProblemBlock.make_dict_of_responses(valid_get_dict)
        assert '2' in result
        assert ['test1', 'test2'] == result['2']

        # If we use [] at the end of a key name, we should always
        # get a list, even if there's just one value
        valid_get_dict = MultiDict({'input_1[]': 'test'})
        result = ProblemBlock.make_dict_of_responses(valid_get_dict)
        assert result['1'] == ['test']

        # If we have no underscores in the name, then the key is invalid
        invalid_get_dict = MultiDict({'input': 'test'})
        with pytest.raises(ValueError):
            result = ProblemBlock.make_dict_of_responses(invalid_get_dict)

        # Two equivalent names (one list, one non-list)
        # One of the values would overwrite the other, so detect this
        # and raise an exception
        invalid_get_dict = MultiDict({'input_1[]': 'test 1',
                                      'input_1': 'test 2'})
        with pytest.raises(ValueError):
            result = ProblemBlock.make_dict_of_responses(invalid_get_dict)

    def test_submit_problem_correct(self):

        module = CapaFactory.create(attempts=1)

        # Simulate that all answers are marked correct, no matter
        # what the input is, by patching CorrectMap.is_correct()
        # Also simulate rendering the HTML
        with patch('xmodule.capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            with patch('xmodule.capa_module.ProblemBlock.get_problem_html') as mock_html:
                mock_is_correct.return_value = True
                mock_html.return_value = "Test HTML"

                # Check the problem
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.submit_problem(get_request_dict)

        # Expect that the problem is marked correct
        assert result['success'] == 'correct'

        # Expect that we get the (mocked) HTML
        assert result['contents'] == 'Test HTML'

        # Expect that the number of attempts is incremented by 1
        assert module.attempts == 2
        # and that this was considered attempt number 2 for grading purposes
        assert module.lcp.context['attempt'] == 2

    def test_submit_problem_incorrect(self):

        module = CapaFactory.create(attempts=0)

        # Simulate marking the input incorrect
        with patch('xmodule.capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = False

            # Check the problem
            get_request_dict = {CapaFactory.input_key(): '0'}
            result = module.submit_problem(get_request_dict)

        # Expect that the problem is marked correct
        assert result['success'] == 'incorrect'

        # Expect that the number of attempts is incremented by 1
        assert module.attempts == 1
        # and that this is considered the first attempt
        assert module.lcp.context['attempt'] == 1

    def test_submit_problem_closed(self):
        module = CapaFactory.create(attempts=3)

        # Problem closed -- cannot submit
        # Simulate that ProblemBlock.closed() always returns True
        with patch('xmodule.capa_module.ProblemBlock.closed') as mock_closed:
            mock_closed.return_value = True
            with pytest.raises(xmodule.exceptions.NotFoundError):
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                module.submit_problem(get_request_dict)

        # Expect that number of attempts NOT incremented
        assert module.attempts == 3

    @ddt.data(
        RANDOMIZATION.ALWAYS,
        'true'
    )
    def test_submit_problem_resubmitted_with_randomize(self, rerandomize):
        # Randomize turned on
        module = CapaFactory.create(rerandomize=rerandomize, attempts=0)

        # Simulate that the problem is completed
        module.done = True

        # Expect that we cannot submit
        with pytest.raises(xmodule.exceptions.NotFoundError):
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            module.submit_problem(get_request_dict)

        # Expect that number of attempts NOT incremented
        assert module.attempts == 0

    @ddt.data(
        RANDOMIZATION.NEVER,
        'false',
        RANDOMIZATION.PER_STUDENT
    )
    def test_submit_problem_resubmitted_no_randomize(self, rerandomize):
        # Randomize turned off
        module = CapaFactory.create(rerandomize=rerandomize, attempts=0, done=True)

        # Expect that we can submit successfully
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        result = module.submit_problem(get_request_dict)

        assert result['success'] == 'correct'

        # Expect that number of attempts IS incremented, still same attempt
        assert module.attempts == 1
        assert module.lcp.context['attempt'] == 1

    def test_submit_problem_queued(self):
        module = CapaFactory.create(attempts=1)

        # Simulate that the problem is queued
        multipatch = patch.multiple(
            'xmodule.capa.capa_problem.LoncapaProblem',
            is_queued=DEFAULT,
            get_recentmost_queuetime=DEFAULT
        )
        with multipatch as values:
            values['is_queued'].return_value = True
            values['get_recentmost_queuetime'].return_value = datetime.datetime.now(UTC)

            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.submit_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            assert 'You must wait' in result['success']

        # Expect that the number of attempts is NOT incremented
        assert module.attempts == 1

    @patch.object(XQueueInterface, '_http_post')
    def test_submit_problem_with_files(self, mock_xqueue_post):
        # Check a problem with uploaded files, using the submit_problem API.
        # pylint: disable=protected-access

        # The files we'll be uploading.
        fnames = ["prog1.py", "prog2.py", "prog3.py"]
        fpaths = [os.path.join(DATA_DIR, "capa", fname) for fname in fnames]
        fileobjs = [open(fpath) for fpath in fpaths]
        for fileobj in fileobjs:
            self.addCleanup(fileobj.close)

        module = CapaFactoryWithFiles.create()

        # Mock the XQueueInterface post method
        mock_xqueue_post.return_value = (0, "ok")

        # Create a request dictionary for submit_problem.
        get_request_dict = {
            CapaFactoryWithFiles.input_key(response_num=2): fileobjs,
            CapaFactoryWithFiles.input_key(response_num=3): 'None',
        }

        module.submit_problem(get_request_dict)

        # pylint: disable=line-too-long
        # _http_post is called like this:
        #   _http_post(
        #       'http://example.com/xqueue/xqueue/submit/',
        #       {
        #           'xqueue_header': '{"lms_key": "df34fb702620d7ae892866ba57572491", "lms_callback_url": "/", "queue_name": "BerkeleyX-cs188x"}',
        #           'xqueue_body': '{"student_info": "{\\"anonymous_student_id\\": \\"student\\", \\"submission_time\\": \\"20131117183318\\"}", "grader_payload": "{\\"project\\": \\"p3\\"}", "student_response": ""}',
        #       },
        #       files={
        #           path(u'/home/ned/edx/edx-platform/common/test/data/uploads/asset.html'):
        #               <open file u'/home/ned/edx/edx-platform/common/test/data/uploads/asset.html', mode 'r' at 0x49c5f60>,
        #           path(u'/home/ned/edx/edx-platform/common/test/data/uploads/image.jpg'):
        #               <open file u'/home/ned/edx/edx-platform/common/test/data/uploads/image.jpg', mode 'r' at 0x49c56f0>,
        #           path(u'/home/ned/edx/edx-platform/common/test/data/uploads/textbook.pdf'):
        #               <open file u'/home/ned/edx/edx-platform/common/test/data/uploads/textbook.pdf', mode 'r' at 0x49c5a50>,
        #       },
        #   )
        # pylint: enable=line-too-long

        assert mock_xqueue_post.call_count == 1
        _, kwargs = mock_xqueue_post.call_args
        self.assertCountEqual(fpaths, list(kwargs['files'].keys()))
        for fpath, fileobj in kwargs['files'].items():
            assert fpath == fileobj.name

    @patch.object(XQueueInterface, '_http_post')
    def test_submit_problem_with_files_as_xblock(self, mock_xqueue_post):
        # Check a problem with uploaded files, using the XBlock API.
        # pylint: disable=protected-access

        # The files we'll be uploading.
        fnames = ["prog1.py", "prog2.py", "prog3.py"]
        fpaths = [os.path.join(DATA_DIR, "capa", fname) for fname in fnames]
        fileobjs = [open(fpath) for fpath in fpaths]
        for fileobj in fileobjs:
            self.addCleanup(fileobj.close)

        module = CapaFactoryWithFiles.create()

        # Mock the XQueueInterface post method
        mock_xqueue_post.return_value = (0, "ok")

        # Create a webob Request with the files uploaded.
        post_data = []
        for fname, fileobj in zip(fnames, fileobjs):
            post_data.append((CapaFactoryWithFiles.input_key(response_num=2), (fname, fileobj)))
        post_data.append((CapaFactoryWithFiles.input_key(response_num=3), 'None'))
        request = webob.Request.blank("/some/fake/url", POST=post_data, content_type='multipart/form-data')

        module.handle('xmodule_handler', request, 'problem_check')

        assert mock_xqueue_post.call_count == 1
        _, kwargs = mock_xqueue_post.call_args
        self.assertCountEqual(fnames, list(kwargs['files'].keys()))
        for fpath, fileobj in kwargs['files'].items():
            assert fpath == fileobj.name

    def test_submit_problem_error(self):

        # Try each exception that capa_module should handle
        exception_classes = [StudentInputError,
                             LoncapaProblemError,
                             ResponseError]
        for exception_class in exception_classes:
            # Create the module
            module = CapaFactory.create(attempts=1, user_is_staff=False)

            # Simulate answering a problem that raises the exception
            with patch('xmodule.capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class('test error')

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.submit_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            expected_msg = 'test error'

            assert expected_msg == result['success']

            # Expect that the number of attempts is NOT incremented
            assert module.attempts == 1
            # but that this was considered attempt number 2 for grading purposes
            assert module.lcp.context['attempt'] == 2

    def test_submit_problem_error_with_codejail_exception(self):

        # Try each exception that capa_module should handle
        exception_classes = [StudentInputError,
                             LoncapaProblemError,
                             ResponseError]
        for exception_class in exception_classes:

            # Create the module
            module = CapaFactory.create(attempts=1, user_is_staff=False)

            # Simulate a codejail exception "Exception: Couldn't execute jailed code"
            with patch('xmodule.capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                try:
                    raise ResponseError(
                        'Couldn\'t execute jailed code: stdout: \'\', '
                        'stderr: \'Traceback (most recent call last):\\n'
                        '  File "jailed_code", line 15, in <module>\\n'
                        '    exec code in g_dict\\n  File "<string>", line 67, in <module>\\n'
                        '  File "<string>", line 65, in check_func\\n'
                        'Exception: Couldn\'t execute jailed code\\n\' with status code: 1', )
                except ResponseError as err:
                    mock_grade.side_effect = exception_class(str(err))
                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.submit_problem(get_request_dict)

            # Expect an AJAX alert message in 'success' without the text of the stack trace
            expected_msg = 'Couldn\'t execute jailed code'
            assert expected_msg == result['success']

            # Expect that the number of attempts is NOT incremented
            assert module.attempts == 1
            # but that this was considered the second attempt for grading purposes
            assert module.lcp.context['attempt'] == 2

    @override_settings(DEBUG=True)
    def test_submit_problem_other_errors(self):
        """
        Test that errors other than the expected kinds give an appropriate message.

        See also `test_submit_problem_error` for the "expected kinds" or errors.
        """
        # Create the module
        module = CapaFactory.create(attempts=1, user_is_staff=False)

        # Simulate answering a problem that raises the exception
        with patch('xmodule.capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
            error_msg = "Superterrible error happened: ☠"
            mock_grade.side_effect = Exception(error_msg)

            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.submit_problem(get_request_dict)

        # Expect an AJAX alert message in 'success'
        assert error_msg in result['success']

    def test_submit_problem_zero_max_grade(self):
        """
        Test that a capa problem with a max grade of zero doesn't generate an error.
        """
        # Create the module
        module = CapaFactory.create(attempts=1)

        # Override the problem score to have a total of zero.
        module.lcp.get_score = lambda: {'score': 0, 'total': 0}

        # Check the problem
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        module.submit_problem(get_request_dict)

    def test_submit_problem_error_nonascii(self):

        # Try each exception that capa_module should handle
        exception_classes = [StudentInputError,
                             LoncapaProblemError,
                             ResponseError]
        for exception_class in exception_classes:
            # Create the module
            module = CapaFactory.create(attempts=1, user_is_staff=False)

            # Simulate answering a problem that raises the exception
            with patch('xmodule.capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class("ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ")

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.submit_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            expected_msg = 'ȧƈƈḗƞŧḗḓ ŧḗẋŧ ƒǿř ŧḗşŧīƞɠ'

            assert expected_msg == result['success']

            # Expect that the number of attempts is NOT incremented
            assert module.attempts == 1
            # but that this was considered the second attempt for grading purposes
            assert module.lcp.context['attempt'] == 2

    def test_submit_problem_error_with_staff_user(self):

        # Try each exception that capa module should handle
        for exception_class in [StudentInputError,
                                LoncapaProblemError,
                                ResponseError]:
            # Create the module
            module = CapaFactory.create(attempts=1, user_is_staff=True)

            # Simulate answering a problem that raises an exception
            with patch('xmodule.capa.capa_problem.LoncapaProblem.grade_answers') as mock_grade:
                mock_grade.side_effect = exception_class('test error')

                get_request_dict = {CapaFactory.input_key(): '3.14'}
                result = module.submit_problem(get_request_dict)

            # Expect an AJAX alert message in 'success'
            assert 'test error' in result['success']

            # We DO include traceback information for staff users
            assert 'Traceback' in result['success']

            # Expect that the number of attempts is NOT incremented
            assert module.attempts == 1
            # but that it was considered the second attempt for grading purposes
            assert module.lcp.context['attempt'] == 2

    @ddt.data(
        ("never", True, None, 'submitted'),
        ("never", False, None, 'submitted'),
        ("past_due", True, None, 'submitted'),
        ("past_due", False, None, 'submitted'),
        ("always", True, 1, 'correct'),
        ("always", False, 0, 'incorrect'),
    )
    @ddt.unpack
    def test_handle_ajax_show_correctness(self, show_correctness, is_correct, expected_score, expected_success):
        module = CapaFactory.create(show_correctness=show_correctness,
                                    due=self.tomorrow_str,
                                    correct=is_correct)

        # Simulate marking the input correct/incorrect
        with patch('xmodule.capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = is_correct

            # Check the problem
            get_request_dict = {CapaFactory.input_key(): '0'}
            json_result = module.handle_ajax('problem_check', get_request_dict)
            result = json.loads(json_result)

        # Expect that the AJAX result withholds correctness and score
        assert result['current_score'] == expected_score
        assert result['success'] == expected_success

        # Expect that the number of attempts is incremented by 1
        assert module.attempts == 1
        assert module.lcp.context['attempt'] == 1

    def test_reset_problem(self):
        module = CapaFactory.create(done=True)
        module.new_lcp = Mock(wraps=module.new_lcp)
        module.choose_new_seed = Mock(wraps=module.choose_new_seed)

        # Stub out HTML rendering
        with patch('xmodule.capa_module.ProblemBlock.get_problem_html') as mock_html:
            mock_html.return_value = "<div>Test HTML</div>"

            # Reset the problem
            get_request_dict = {}
            result = module.reset_problem(get_request_dict)

        # Expect that the request was successful
        assert (('success' in result) and result['success'])

        # Expect that the problem HTML is retrieved
        assert 'html' in result
        assert result['html'] == '<div>Test HTML</div>'

        # Expect that the problem was reset
        module.new_lcp.assert_called_once_with(None)

    def test_reset_problem_closed(self):
        # pre studio default
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS)

        # Simulate that the problem is closed
        with patch('xmodule.capa_module.ProblemBlock.closed') as mock_closed:
            mock_closed.return_value = True

            # Try to reset the problem
            get_request_dict = {}
            result = module.reset_problem(get_request_dict)

        # Expect that the problem was NOT reset
        assert (('success' in result) and (not result['success']))

    def test_reset_problem_not_done(self):
        # Simulate that the problem is NOT done
        module = CapaFactory.create(done=False)

        # Try to reset the problem
        get_request_dict = {}
        result = module.reset_problem(get_request_dict)

        # Expect that the problem was NOT reset
        assert (('success' in result) and (not result['success']))

    def test_rescore_problem_correct(self):

        module = CapaFactory.create(attempts=0, done=True)

        # Simulate that all answers are marked correct, no matter
        # what the input is, by patching LoncapaResponse.evaluate_answers()
        with patch('xmodule.capa.responsetypes.LoncapaResponse.evaluate_answers') as mock_evaluate_answers:
            mock_evaluate_answers.return_value = CorrectMap(
                answer_id=CapaFactory.answer_key(),
                correctness='correct',
                npoints=1,
            )
            with patch('xmodule.capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
                mock_is_correct.return_value = True

                # Check the problem
                get_request_dict = {CapaFactory.input_key(): '1'}
                module.submit_problem(get_request_dict)
            module.rescore(only_if_higher=False)

        # Expect that the problem is marked correct
        assert module.is_correct() is True

        # Expect that the number of attempts is not incremented
        assert module.attempts == 1
        # and that this was considered attempt number 1 for grading purposes
        assert module.lcp.context['attempt'] == 1

    def test_rescore_problem_additional_correct(self):
        # make sure it also works when new correct answer has been added
        module = CapaFactory.create(attempts=0)
        answer_id = CapaFactory.answer_key()

        # Check the problem
        get_request_dict = {CapaFactory.input_key(): '1'}
        result = module.submit_problem(get_request_dict)

        # Expect that the problem is marked incorrect and user didn't earn score
        assert result['success'] == 'incorrect'
        assert module.get_score() == (0, 1)
        assert module.correct_map[answer_id]['correctness'] == 'incorrect'

        # Expect that the number of attempts has incremented to 1
        assert module.attempts == 1
        assert module.lcp.context['attempt'] == 1

        # Simulate that after making an incorrect answer to the correct answer
        # the new calculated score is (1,1)
        # by patching CorrectMap.is_correct() and NumericalResponse.get_staff_ans()
        # In case of rescore with only_if_higher=True it should update score of module
        # if previous score was lower

        with patch('xmodule.capa.correctmap.CorrectMap.is_correct') as mock_is_correct:
            mock_is_correct.return_value = True
            module.set_score(module.score_from_lcp(module.lcp))
            with patch('xmodule.capa.responsetypes.NumericalResponse.get_staff_ans') as get_staff_ans:
                get_staff_ans.return_value = 1 + 0j
                module.rescore(only_if_higher=True)

        # Expect that the problem is marked correct and user earned the score
        assert module.get_score() == (1, 1)
        assert module.correct_map[answer_id]['correctness'] == 'correct'
        # Expect that the number of attempts is not incremented
        assert module.attempts == 1
        # and hence that this was still considered the first attempt for grading purposes
        assert module.lcp.context['attempt'] == 1

    def test_rescore_problem_incorrect(self):
        # make sure it also works when attempts have been reset,
        # so add this to the test:
        module = CapaFactory.create(attempts=0, done=True)

        # Simulate that all answers are marked incorrect, no matter
        # what the input is, by patching LoncapaResponse.evaluate_answers()
        with patch('xmodule.capa.responsetypes.LoncapaResponse.evaluate_answers') as mock_evaluate_answers:
            mock_evaluate_answers.return_value = CorrectMap(CapaFactory.answer_key(), 'incorrect')
            module.rescore(only_if_higher=False)

        # Expect that the problem is marked incorrect
        assert module.is_correct() is False

        # Expect that the number of attempts is not incremented
        assert module.attempts == 0
        # and that this is treated as the first attempt for grading purposes
        assert module.lcp.context['attempt'] == 1

    def test_rescore_problem_not_done(self):
        # Simulate that the problem is NOT done
        module = CapaFactory.create(done=False)

        # Try to rescore the problem, and get exception
        with pytest.raises(xmodule.exceptions.NotFoundError):
            module.rescore(only_if_higher=False)

    def test_rescore_problem_not_supported(self):
        module = CapaFactory.create(done=True)

        # Try to rescore the problem, and get exception
        with patch('xmodule.capa.capa_problem.LoncapaProblem.supports_rescoring') as mock_supports_rescoring:
            mock_supports_rescoring.return_value = False
            with pytest.raises(NotImplementedError):
                module.rescore(only_if_higher=False)

    def capa_factory_for_problem_xml(self, xml):  # lint-amnesty, pylint: disable=missing-function-docstring
        class CustomCapaFactory(CapaFactory):
            """
            A factory for creating a Capa problem with arbitrary xml.
            """
            sample_problem_xml = textwrap.dedent(xml)

        return CustomCapaFactory

    def test_codejail_error_upon_problem_creation(self):
        # Simulate a codejail safe_exec failure upon problem creation.
        # Create a problem with some script attached.
        xml_str = textwrap.dedent("""
            <problem>
                <script>test=True</script>
            </problem>
        """)
        factory = self.capa_factory_for_problem_xml(xml_str)

        # When codejail safe_exec fails upon problem creation, a LoncapaProblemError should be raised.
        with pytest.raises(LoncapaProblemError):
            with patch('xmodule.capa.capa_problem.safe_exec') as mock_safe_exec:
                mock_safe_exec.side_effect = SafeExecException()
                factory.create()

    def _rescore_problem_error_helper(self, exception_class):
        """Helper to allow testing all errors that rescoring might return."""
        # Create the module
        module = CapaFactory.create(attempts=1, done=True)

        # Simulate answering a problem that raises the exception
        with patch('xmodule.capa.capa_problem.LoncapaProblem.get_grade_from_current_answers') as mock_rescore:
            mock_rescore.side_effect = exception_class('test error \u03a9')
            with pytest.raises(exception_class):
                module.rescore(only_if_higher=False)

        # Expect that the number of attempts is NOT incremented
        assert module.attempts == 1
        # and that this was considered the first attempt for grading purposes
        assert module.lcp.context['attempt'] == 1

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
        assert module.lcp.student_answers == expected_answers

        # Expect that the result is success
        assert (('success' in result) and result['success'])

    def test_save_problem_closed(self):
        module = CapaFactory.create(done=False)

        # Simulate that the problem is closed
        with patch('xmodule.capa_module.ProblemBlock.closed') as mock_closed:
            mock_closed.return_value = True

            # Try to save the problem
            get_request_dict = {CapaFactory.input_key(): '3.14'}
            result = module.save_problem(get_request_dict)

        # Expect that the result is failure
        assert (('success' in result) and (not result['success']))

    @ddt.data(
        RANDOMIZATION.ALWAYS,
        'true'
    )
    def test_save_problem_submitted_with_randomize(self, rerandomize):
        # Capa XModule treats 'always' and 'true' equivalently
        module = CapaFactory.create(rerandomize=rerandomize, done=True)

        # Try to save
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        result = module.save_problem(get_request_dict)

        # Expect that we cannot save
        assert (('success' in result) and (not result['success']))

    @ddt.data(
        RANDOMIZATION.NEVER,
        'false',
        RANDOMIZATION.PER_STUDENT
    )
    def test_save_problem_submitted_no_randomize(self, rerandomize):
        # Capa XModule treats 'false' and 'per_student' equivalently
        module = CapaFactory.create(rerandomize=rerandomize, done=True)

        # Try to save
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        result = module.save_problem(get_request_dict)

        # Expect that we succeed
        assert (('success' in result) and result['success'])

    def test_submit_button_name(self):
        module = CapaFactory.create(attempts=0)
        assert module.submit_button_name() == 'Submit'

    def test_submit_button_submitting_name(self):
        module = CapaFactory.create(attempts=1, max_attempts=10)
        assert module.submit_button_submitting_name() == 'Submitting'

    def test_should_enable_submit_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, disable the submit button
        module = CapaFactory.create(due=self.yesterday_str)
        assert not module.should_enable_submit_button()

        # If user is out of attempts, disable the submit button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts)
        assert not module.should_enable_submit_button()

        # If survey question (max_attempts = 0), disable the submit button
        module = CapaFactory.create(max_attempts=0)
        assert not module.should_enable_submit_button()

        # If user submitted a problem but hasn't reset,
        # disable the submit button
        # Note:  we can only reset when rerandomize="always" or "true"
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, done=True)
        assert not module.should_enable_submit_button()

        module = CapaFactory.create(rerandomize="true", done=True)
        assert not module.should_enable_submit_button()

        # Otherwise, enable the submit button
        module = CapaFactory.create()
        assert module.should_enable_submit_button()

        # If the user has submitted the problem
        # and we do NOT have a reset button, then we can enable the submit button
        # Setting rerandomize to "never" or "false" ensures that the reset button
        # is not shown
        module = CapaFactory.create(rerandomize=RANDOMIZATION.NEVER, done=True)
        assert module.should_enable_submit_button()

        module = CapaFactory.create(rerandomize="false", done=True)
        assert module.should_enable_submit_button()

        module = CapaFactory.create(rerandomize=RANDOMIZATION.PER_STUDENT, done=True)
        assert module.should_enable_submit_button()

    def test_should_show_reset_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, do NOT show the reset button
        module = CapaFactory.create(due=self.yesterday_str, done=True)
        assert not module.should_show_reset_button()

        # If the user is out of attempts, do NOT show the reset button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts, done=True)
        assert not module.should_show_reset_button()

        # pre studio default value, DO show the reset button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, done=True)
        assert module.should_show_reset_button()

        # If survey question for capa (max_attempts = 0),
        # DO show the reset button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, max_attempts=0, done=True)
        assert module.should_show_reset_button()

        # If the question is not correct
        # DO show the reset button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, max_attempts=0, done=True, correct=False)
        assert module.should_show_reset_button()

        # If the question is correct and randomization is never
        # DO not show the reset button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.NEVER, max_attempts=0, done=True, correct=True)
        assert not module.should_show_reset_button()

        # If the question is correct and randomization is always
        # Show the reset button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, max_attempts=0, done=True, correct=True)
        assert module.should_show_reset_button()

        # Don't show reset button if randomization is turned on and the question is not done
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, show_reset_button=False, done=False)
        assert not module.should_show_reset_button()

        # Show reset button if randomization is turned on and the problem is done
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, show_reset_button=False, done=True)
        assert module.should_show_reset_button()

    def test_should_show_save_button(self):

        attempts = random.randint(1, 10)

        # If we're after the deadline, do NOT show the save button
        module = CapaFactory.create(due=self.yesterday_str, done=True)
        assert not module.should_show_save_button()

        # If the user is out of attempts, do NOT show the save button
        module = CapaFactory.create(attempts=attempts, max_attempts=attempts, done=True)
        assert not module.should_show_save_button()

        # If user submitted a problem but hasn't reset, do NOT show the save button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, done=True)
        assert not module.should_show_save_button()

        module = CapaFactory.create(rerandomize="true", done=True)
        assert not module.should_show_save_button()

        # If the user has unlimited attempts and we are not randomizing,
        # then do NOT show a save button
        # because they can keep using "Check"
        module = CapaFactory.create(max_attempts=None, rerandomize=RANDOMIZATION.NEVER, done=False)
        assert not module.should_show_save_button()

        module = CapaFactory.create(max_attempts=None, rerandomize="false", done=True)
        assert not module.should_show_save_button()

        module = CapaFactory.create(max_attempts=None, rerandomize=RANDOMIZATION.PER_STUDENT, done=True)
        assert not module.should_show_save_button()

        # pre-studio default, DO show the save button
        module = CapaFactory.create(rerandomize=RANDOMIZATION.ALWAYS, done=False)
        assert module.should_show_save_button()

        # If we're not randomizing and we have limited attempts,  then we can save
        module = CapaFactory.create(rerandomize=RANDOMIZATION.NEVER, max_attempts=2, done=True)
        assert module.should_show_save_button()

        module = CapaFactory.create(rerandomize="false", max_attempts=2, done=True)
        assert module.should_show_save_button()

        module = CapaFactory.create(rerandomize=RANDOMIZATION.PER_STUDENT, max_attempts=2, done=True)
        assert module.should_show_save_button()

        # If survey question for capa (max_attempts = 0),
        # DO show the save button
        module = CapaFactory.create(max_attempts=0, done=False)
        assert module.should_show_save_button()

    def test_should_show_save_button_force_save_button(self):
        # If we're after the deadline, do NOT show the save button
        # even though we're forcing a save
        module = CapaFactory.create(due=self.yesterday_str,
                                    force_save_button="true",
                                    done=True)
        assert not module.should_show_save_button()

        # If the user is out of attempts, do NOT show the save button
        attempts = random.randint(1, 10)
        module = CapaFactory.create(attempts=attempts,
                                    max_attempts=attempts,
                                    force_save_button="true",
                                    done=True)
        assert not module.should_show_save_button()

        # Otherwise, if we force the save button,
        # then show it even if we would ordinarily
        # require a reset first
        module = CapaFactory.create(force_save_button="true",
                                    rerandomize=RANDOMIZATION.ALWAYS,
                                    done=True)
        assert module.should_show_save_button()

        module = CapaFactory.create(force_save_button="true",
                                    rerandomize="true",
                                    done=True)
        assert module.should_show_save_button()

    def test_no_max_attempts(self):
        module = CapaFactory.create(max_attempts='')
        html = module.get_problem_html()
        assert html is not None
        # assert that we got here without exploding

    def test_get_problem_html(self):
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(render_template=render_template)

        # We've tested the show/hide button logic in other tests,
        # so here we hard-wire the values
        enable_submit_button = bool(random.randint(0, 1) % 2)
        show_reset_button = bool(random.randint(0, 1) % 2)
        show_save_button = bool(random.randint(0, 1) % 2)

        module.should_enable_submit_button = Mock(return_value=enable_submit_button)
        module.should_show_reset_button = Mock(return_value=show_reset_button)
        module.should_show_save_button = Mock(return_value=show_save_button)

        # Patch the capa problem's HTML rendering
        with patch('xmodule.capa.capa_problem.LoncapaProblem.get_html') as mock_html:
            mock_html.return_value = "<div>Test Problem HTML</div>"

            # Render the problem HTML
            html = module.get_problem_html(encapsulate=False)

            # Also render the problem encapsulated in a <div>
            html_encapsulated = module.get_problem_html(encapsulate=True)

        # Expect that we get the rendered template back
        assert html == '<div>Test Template HTML</div>'

        # Check the rendering context
        render_args, _ = render_template.call_args
        assert len(render_args) == 2

        template_name = render_args[0]
        assert template_name == 'problem.html'

        context = render_args[1]
        assert context['problem']['html'] == '<div>Test Problem HTML</div>'
        assert bool(context['should_enable_submit_button']) == enable_submit_button
        assert bool(context['reset_button']) == show_reset_button
        assert bool(context['save_button']) == show_save_button
        assert not context['demand_hint_possible']

        # Assert that the encapsulated html contains the original html
        assert html in html_encapsulated

    demand_xml = """
        <problem>
        <p>That is the question</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">Alpha <choicehint>A hint</choicehint>
            </choice>
            <choice correct="true">Beta</choice>
          </choicegroup>
        </multiplechoiceresponse>
        <demandhint>
          <hint>Demand 1</hint>
          <hint>Demand 2</hint>
        </demandhint>
        </problem>"""

    def test_demand_hint(self):
        # HTML generation is mocked out to be meaningless here, so instead we check
        # the context dict passed into HTML generation.
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(xml=self.demand_xml, render_template=render_template)
        module.get_problem_html()  # ignoring html result
        context = render_template.call_args[0][1]
        assert context['demand_hint_possible']
        assert context['should_enable_next_hint']

        # Check the AJAX call that gets the hint by index
        result = module.get_demand_hint(0)
        assert result['hint_index'] == 0
        assert result['should_enable_next_hint']

        result = module.get_demand_hint(1)
        assert result['hint_index'] == 1
        assert not result['should_enable_next_hint']

        result = module.get_demand_hint(2)  # here the server wraps around to index 0
        assert result['hint_index'] == 0
        assert result['should_enable_next_hint']

    def test_single_demand_hint(self):
        """
        Test the hint button enabled state when there is just a single hint.
        """
        test_xml = """
            <problem>
            <p>That is the question</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">Alpha <choicehint>A hint</choicehint>
                </choice>
                <choice correct="true">Beta</choice>
              </choicegroup>
            </multiplechoiceresponse>
            <demandhint>
              <hint>Only demand hint</hint>
            </demandhint>
            </problem>"""
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(xml=test_xml, render_template=render_template)
        module.get_problem_html()  # ignoring html result
        context = render_template.call_args[0][1]
        assert context['demand_hint_possible']
        assert context['should_enable_next_hint']

        # Check the AJAX call that gets the hint by index
        result = module.get_demand_hint(0)
        assert result['hint_index'] == 0
        assert not result['should_enable_next_hint']

    def test_image_hint(self):
        """
        Test the hint button shows an image without the static url.
        """
        test_xml = """
            <problem>
            <p>That is the question</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">Alpha <choicehint>A hint</choicehint>
                </choice>
                <choice correct="true">Beta</choice>
              </choicegroup>
            </multiplechoiceresponse>
            <demandhint>
              <hint>
                <img src="/static/7b1d74b2383b7d25a70ae4991190c222_28-collection-of-dark-souls-bonfire-clipart-high-quality-free-_1200-1386.jpeg"> </img>
                You can add an optional hint like this. Problems that have a hint include a hint button, and this text appears the first time learners select the button.</hint>
            </demandhint>
            </problem>"""
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(xml=test_xml, render_template=render_template)
        module.get_problem_html()  # ignoring html result
        context = render_template.call_args[0][1]
        assert context['demand_hint_possible']
        assert context['should_enable_next_hint']

        # Check the AJAX call that gets the hint by index
        result = module.get_demand_hint(0)
        assert result['hint_index'] == 0
        assert not result['should_enable_next_hint']

    def test_demand_hint_logging(self):
        """
        Test calling get_demand_hunt() results in an event being published.
        """
        module = CapaFactory.create(xml=self.demand_xml)
        with patch.object(module.runtime, 'publish') as mock_track_function:
            module.get_problem_html()
            module.get_demand_hint(0)
            mock_track_function.assert_called_with(
                module, 'edx.problem.hint.demandhint_displayed',
                {'hint_index': 0, 'module_id': str(module.location),
                 'hint_text': 'Demand 1', 'hint_len': 2}
            )

    def test_input_state_consistency(self):
        module1 = CapaFactory.create()
        module2 = CapaFactory.create()

        # check to make sure that the input_state and the keys have the same values
        module1.set_state_from_lcp()
        assert list(module1.lcp.inputs.keys()) == list(module1.input_state.keys())

        module2.set_state_from_lcp()

        intersection = set(module2.input_state.keys()).intersection(set(module1.input_state.keys()))
        assert len(intersection) == 0

    def test_get_problem_html_error(self):
        """
        In production, when an error occurs with the problem HTML
        rendering, a "dummy" problem is created with an error
        message to display to the user.
        """
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(render_template=render_template)

        # Save the original problem so we can compare it later
        original_problem = module.lcp

        # Simulate throwing an exception when the capa problem
        # is asked to render itself as HTML
        module.lcp.get_html = Mock(side_effect=Exception("Test"))

        # Try to render the module with DEBUG turned off
        html = module.get_problem_html()

        assert html is not None

        # Check the rendering context
        render_args, _ = render_template.call_args
        context = render_args[1]
        assert 'error' in context['problem']['html']

        # Expect that the module has created a new dummy problem with the error
        assert original_problem != module.lcp

    def test_get_problem_html_error_preview(self):
        """
        Test the html response when an error occurs with DEBUG off in Studio.
        """
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(render_template=render_template)

        # Simulate throwing an exception when the capa problem
        # is asked to render itself as HTML
        error_msg = "Superterrible error happened: ☠"
        module.lcp.get_html = Mock(side_effect=Exception(error_msg))

        module.system.is_author_mode = True

        # Try to render the module with the author mode turned on
        html = module.get_problem_html()

        assert html is not None

        # Check the rendering context
        render_args, _ = render_template.call_args
        context = render_args[1]
        assert error_msg in context['problem']['html']

    @override_settings(DEBUG=True)
    def test_get_problem_html_error_w_debug(self):
        """
        Test the html response when an error occurs with DEBUG on
        """
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(render_template=render_template)

        # Simulate throwing an exception when the capa problem
        # is asked to render itself as HTML
        error_msg = "Superterrible error happened: ☠"
        module.lcp.get_html = Mock(side_effect=Exception(error_msg))

        # Try to render the module with DEBUG turned on
        html = module.get_problem_html()

        assert html is not None

        # Check the rendering context
        render_args, _ = render_template.call_args
        context = render_args[1]
        assert error_msg in context['problem']['html']

    @ddt.data(
        'false',
        'true',
        RANDOMIZATION.NEVER,
        RANDOMIZATION.PER_STUDENT,
        RANDOMIZATION.ALWAYS,
        RANDOMIZATION.ONRESET
    )
    def test_random_seed_no_change(self, rerandomize):

        # Run the test for each possible rerandomize value

        module = CapaFactory.create(rerandomize=rerandomize)

        # Get the seed
        # By this point, the module should have persisted the seed
        seed = module.seed
        assert seed is not None

        # If we're not rerandomizing, the seed is always set
        # to the same value (1)
        if rerandomize == RANDOMIZATION.NEVER:
            assert seed == 1, "Seed should always be 1 when rerandomize='%s'" % rerandomize

        # Check the problem
        get_request_dict = {CapaFactory.input_key(): '3.14'}
        module.submit_problem(get_request_dict)

        # Expect that the seed is the same
        assert seed == module.seed

        # Save the problem
        module.save_problem(get_request_dict)

        # Expect that the seed is the same
        assert seed == module.seed

    @ddt.data(
        'false',
        'true',
        RANDOMIZATION.NEVER,
        RANDOMIZATION.PER_STUDENT,
        RANDOMIZATION.ALWAYS,
        RANDOMIZATION.ONRESET
    )
    def test_random_seed_with_reset(self, rerandomize):
        """
        Run the test for each possible rerandomize value
        """

        def _reset_and_get_seed(module):
            """
            Reset the XModule and return the module's seed
            """

            # Simulate submitting an attempt
            # We need to do this, or reset_problem() will
            # fail because it won't re-randomize until the problem has been submitted
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
            for __ in range(num_tries):
                if test_func() is True:
                    success = True
                    break
            return success

        module = CapaFactory.create(rerandomize=rerandomize, done=True)

        # Get the seed
        # By this point, the module should have persisted the seed
        seed = module.seed
        assert seed is not None

        # We do NOT want the seed to reset if rerandomize
        # is set to 'never' -- it should still be 1
        # The seed also stays the same if we're randomizing
        # 'per_student': the same student should see the same problem
        if rerandomize in [RANDOMIZATION.NEVER,
                           'false',
                           RANDOMIZATION.PER_STUDENT]:
            assert seed == _reset_and_get_seed(module)

        # Otherwise, we expect the seed to change
        # to another valid seed
        else:

            # Since there's a small chance (expected) we might get the
            # same seed again, give it 10 chances
            # to generate a different seed
            success = _retry_and_check(10, lambda: _reset_and_get_seed(module) != seed)

            assert module.seed is not None
            msg = 'Could not get a new seed from reset after 10 tries'
            assert success, msg

    @ddt.data(
        'false',
        'true',
        RANDOMIZATION.NEVER,
        RANDOMIZATION.PER_STUDENT,
        RANDOMIZATION.ALWAYS,
        RANDOMIZATION.ONRESET
    )
    def test_random_seed_with_reset_question_unsubmitted(self, rerandomize):
        """
        Run the test for each possible rerandomize value
        """

        def _reset_and_get_seed(module):
            """
            Reset the XModule and return the module's seed
            """

            # Reset the problem
            # By default, the problem is instantiated as unsubmitted
            module.reset_problem({})

            # Return the seed
            return module.seed

        module = CapaFactory.create(rerandomize=rerandomize, done=False)

        # Get the seed
        # By this point, the module should have persisted the seed
        seed = module.seed
        assert seed is not None

        # the seed should never change because the student hasn't finished the problem
        assert seed == _reset_and_get_seed(module)

    @ddt.data(
        RANDOMIZATION.ALWAYS,
        RANDOMIZATION.PER_STUDENT,
        'true',
        RANDOMIZATION.ONRESET
    )
    def test_random_seed_bins(self, rerandomize):
        # Assert that we are limiting the number of possible seeds.
        # Get a bunch of seeds, they should all be in 0-999.
        i = 200
        while i > 0:
            module = CapaFactory.create(rerandomize=rerandomize)
            assert 0 <= module.seed < 1000
            i -= 1

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
            assert module.get_progress() is None
            mock_log.exception.assert_called_once_with('Got bad progress')
            mock_log.reset_mock()

    @patch('xmodule.capa_module.Progress')
    def test_get_progress_no_error_if_weight_zero(self, mock_progress):
        """
        Check that if the weight is 0 get_progress does not try to create a Progress object.
        """
        mock_progress.return_value = True
        module = CapaFactory.create()
        module.weight = 0
        progress = module.get_progress()
        assert progress is None
        assert not mock_progress.called

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

    @ddt.data(
        ("never", True, None),
        ("never", False, None),
        ("past_due", True, None),
        ("past_due", False, None),
        ("always", True, 1),
        ("always", False, 0),
    )
    @ddt.unpack
    def test_get_display_progress_show_correctness(self, show_correctness, is_correct, expected_score):
        """
        Check that score and total are calculated correctly for the progress fraction.
        """
        module = CapaFactory.create(correct=is_correct,
                                    show_correctness=show_correctness,
                                    due=self.tomorrow_str)
        module.weight = 1
        score, total = module.get_display_progress()
        assert score == expected_score
        assert total == 1

    def test_get_html(self):
        """
        Check that get_html() calls get_progress() with no arguments.
        """
        module = CapaFactory.create()
        module.get_progress = Mock(wraps=module.get_progress)
        module.get_html()
        module.get_progress.assert_called_with()

    def test_get_problem(self):
        """
        Check that get_problem() returns the expected dictionary.
        """
        module = CapaFactory.create()
        assert module.get_problem('data') == {'html': module.get_problem_html(encapsulate=False)}

    # Standard question with shuffle="true" used by a few tests
    common_shuffle_xml = textwrap.dedent("""
        <problem>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice" shuffle="true">
            <choice correct="false">Apple</choice>
            <choice correct="false">Banana</choice>
            <choice correct="false">Chocolate</choice>
            <choice correct ="true">Donut</choice>
          </choicegroup>
        </multiplechoiceresponse>
        </problem>
    """)

    def test_check_unmask(self):
        """
        Check that shuffle unmasking is plumbed through: when submit_problem is called,
        unmasked names should appear in the track_function event_info.
        """
        module = CapaFactory.create(xml=self.common_shuffle_xml)
        with patch.object(module.runtime, 'publish') as mock_track_function:
            get_request_dict = {CapaFactory.input_key(): 'choice_3'}  # the correct choice
            module.submit_problem(get_request_dict)
            mock_call = mock_track_function.mock_calls[1]
            event_info = mock_call[1][2]
            assert event_info['answers'][CapaFactory.answer_key()] == 'choice_3'
            # 'permutation' key added to record how problem was shown
            assert event_info['permutation'][CapaFactory.answer_key()] ==\
                   ('shuffle', ['choice_3', 'choice_1', 'choice_2', 'choice_0'])
            assert event_info['success'] == 'correct'

    @unittest.skip("masking temporarily disabled")
    def test_save_unmask(self):
        """On problem save, unmasked data should appear on track_function."""
        module = CapaFactory.create(xml=self.common_shuffle_xml)
        with patch.object(module.runtime, 'track_function') as mock_track_function:
            get_request_dict = {CapaFactory.input_key(): 'mask_0'}
            module.save_problem(get_request_dict)
            mock_call = mock_track_function.mock_calls[0]
            event_info = mock_call[1][1]
            assert event_info['answers'][CapaFactory.answer_key()] == 'choice_2'
            assert event_info['permutation'][CapaFactory.answer_key()] is not None

    @unittest.skip("masking temporarily disabled")
    def test_reset_unmask(self):
        """On problem reset, unmask names should appear track_function."""
        module = CapaFactory.create(xml=self.common_shuffle_xml)
        get_request_dict = {CapaFactory.input_key(): 'mask_0'}
        module.submit_problem(get_request_dict)
        # On reset, 'old_state' should use unmasked names
        with patch.object(module.runtime, 'track_function') as mock_track_function:
            module.reset_problem(None)
            mock_call = mock_track_function.mock_calls[0]
            event_info = mock_call[1][1]
            assert mock_call[1][0] == 'reset_problem'
            assert event_info['old_state']['student_answers'][CapaFactory.answer_key()] == 'choice_2'
            assert event_info['permutation'][CapaFactory.answer_key()] is not None

    @unittest.skip("masking temporarily disabled")
    def test_rescore_unmask(self):
        """On problem rescore, unmasked names should appear on track_function."""
        module = CapaFactory.create(xml=self.common_shuffle_xml)
        get_request_dict = {CapaFactory.input_key(): 'mask_0'}
        module.submit_problem(get_request_dict)
        # On rescore, state/student_answers should use unmasked names
        with patch.object(module.runtime, 'track_function') as mock_track_function:
            module.rescore_problem(only_if_higher=False)  # lint-amnesty, pylint: disable=no-member
            mock_call = mock_track_function.mock_calls[0]
            event_info = mock_call[1][1]
            assert mock_call[1][0] == 'problem_rescore'
            assert event_info['state']['student_answers'][CapaFactory.answer_key()] == 'choice_2'
            assert event_info['permutation'][CapaFactory.answer_key()] is not None

    def test_check_unmask_answerpool(self):
        """Check answer-pool question track_function uses unmasked names"""
        xml = textwrap.dedent("""
            <problem>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">Apple</choice>
                <choice correct="false">Banana</choice>
                <choice correct="false">Chocolate</choice>
                <choice correct ="true">Donut</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        module = CapaFactory.create(xml=xml)
        with patch.object(module.runtime, 'publish') as mock_track_function:
            get_request_dict = {CapaFactory.input_key(): 'choice_2'}  # mask_X form when masking enabled
            module.submit_problem(get_request_dict)
            mock_call = mock_track_function.mock_calls[1]
            event_info = mock_call[1][2]
            assert event_info['answers'][CapaFactory.answer_key()] == 'choice_2'
            # 'permutation' key added to record how problem was shown
            assert event_info['permutation'][CapaFactory.answer_key()] ==\
                   ('answerpool', ['choice_1', 'choice_3', 'choice_2', 'choice_0'])
            assert event_info['success'] == 'incorrect'

    @ddt.unpack
    @ddt.data(
        {'display_name': None, 'expected_display_name': 'problem'},
        {'display_name': '', 'expected_display_name': 'problem'},
        {'display_name': ' ', 'expected_display_name': 'problem'},
        {'display_name': 'CAPA 101', 'expected_display_name': 'CAPA 101'}
    )
    def test_problem_display_name_with_default(self, display_name, expected_display_name):
        """
        Verify that display_name_with_default works as expected.
        """
        module = CapaFactory.create(display_name=display_name)
        assert module.display_name_with_default == expected_display_name

    @ddt.data(
        '',
        '   ',
    )
    def test_problem_no_display_name(self, display_name):
        """
        Verify that if problem display name is not provided then a default name is used.
        """
        render_template = Mock(return_value="<div>Test Template HTML</div>")
        module = CapaFactory.create(display_name=display_name, render_template=render_template)
        module.get_problem_html()
        render_args, _ = render_template.call_args
        context = render_args[1]
        assert context['problem']['name'] == module.location.block_type


@ddt.ddt
class ProblemBlockXMLTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring
    sample_checkbox_problem_xml = textwrap.dedent("""
        <problem>
            <p>Title</p>

            <p>Description</p>

            <p>Example</p>

            <p>The following languages are in the Indo-European family:</p>
            <choiceresponse>
              <checkboxgroup>
                <choice correct="true">Urdu</choice>
                <choice correct="false">Finnish</choice>
                <choice correct="true">Marathi</choice>
                <choice correct="true">French</choice>
                <choice correct="false">Hungarian</choice>
              </checkboxgroup>
            </choiceresponse>

            <p>Note: Make sure you select all of the correct options—there may be more than one!</p>

            <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p>Solution for CAPA problem</p>

            </div>
            </solution>

        </problem>
    """)

    sample_dropdown_problem_xml = textwrap.dedent("""
        <problem>
            <p>Dropdown problems allow learners to select only one option from a list of options.</p>

            <p>Description</p>

            <p>You can use the following example problem as a model.</p>

            <p> Which of the following countries celebrates its independence on August 15?</p>


            <optionresponse>
              <optioninput options="('India','Spain','China','Bermuda')" correct="India"></optioninput>
            </optionresponse>

             <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p> India became an independent nation on August 15, 1947.</p>

            </div>
            </solution>

        </problem>
    """)

    sample_multichoice_problem_xml = textwrap.dedent("""
        <problem>
            <p>Multiple choice problems allow learners to select only one option.</p>

            <p>When you add the problem, be sure to select Settings to specify a Display Name and other values.</p>

            <p>You can use the following example problem as a model.</p>

            <p>Which of the following countries has the largest population?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">Brazil
                    <choicehint>timely feedback -- explain why an almost correct answer is wrong</choicehint>
                </choice>
                <choice correct="false">Germany</choice>
                <choice correct="true">Indonesia</choice>
                <choice correct="false">Russia</choice>
              </choicegroup>
            </multiplechoiceresponse>

            <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p>According to September 2014 estimates:</p>
            <p>The population of Indonesia is approximately 250 million.</p>
            <p>The population of Brazil  is approximately 200 million.</p>
            <p>The population of Russia is approximately 146 million.</p>
            <p>The population of Germany is approximately 81 million.</p>

            </div>
            </solution>

        </problem>
    """)

    sample_numerical_input_problem_xml = textwrap.dedent("""
        <problem>
            <p>In a numerical input problem, learners enter numbers or a specific and relatively simple mathematical
            expression. Learners enter the response in plain text, and the system then converts the text to a symbolic
            expression that learners can see below the response field.</p>

            <p>The system can handle several types of characters, including basic operators, fractions, exponents, and
            common constants such as "i". You can refer learners to "Entering Mathematical and Scientific Expressions"
            in the edX Guide for Students for more information.</p>

            <p>When you add the problem, be sure to select Settings to specify a Display Name and other values that
            apply.</p>

            <p>You can use the following example problems as models.</p>

            <p>How many miles away from Earth is the sun? Use scientific notation to answer.</p>

            <numericalresponse answer="9.3*10^7">
              <formulaequationinput/>
            </numericalresponse>

            <p>The square of what number is -100?</p>

            <numericalresponse answer="10*i">
              <formulaequationinput/>
            </numericalresponse>

            <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p>The sun is 93,000,000, or 9.3*10^7, miles away from Earth.</p>
            <p>-100 is the square of 10 times the imaginary number, i.</p>

            </div>
            </solution>

        </problem>
    """)

    sample_text_input_problem_xml = textwrap.dedent("""
        <problem>
            <p>In text input problems, also known as "fill-in-the-blank" problems, learners enter text into a response
            field. The text can include letters and characters such as punctuation marks. The text that the learner
            enters must match your specified answer text exactly. You can specify more than one correct answer.
            Learners must enter a response that matches one of the correct answers exactly.</p>

            <p>When you add the problem, be sure to select Settings to specify a Display Name and other values that
            apply.</p>

            <p>You can use the following example problem as a model.</p>

            <p>What was the first post-secondary school in China to allow both male and female students?</p>

            <stringresponse answer="Nanjing Higher Normal Institute" type="ci" >
              <additional_answer answer="National Central University"></additional_answer>
              <additional_answer answer="Nanjing University"></additional_answer>
              <textline size="20"/>
            </stringresponse>

            <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p>Nanjing Higher Normal Institute first admitted female students in 1920.</p>

            </div>
            </solution>

        </problem>
    """)

    sample_checkboxes_with_hints_and_feedback_problem_xml = textwrap.dedent("""
        <problem>
            <p>You can provide feedback for each option in a checkbox problem, with distinct feedback depending on
            whether or not the learner selects that option.</p>

            <p>You can also provide compound feedback for a specific combination of answers. For example, if you have
            three possible answers in the problem, you can configure specific feedback for when a learner selects each
            combination of possible answers.</p>

            <p>You can also add hints for learners.</p>

            <p>Be sure to select Settings to specify a Display Name and other values that apply.</p>

            <p>Use the following example problem as a model.</p>

            <p>Which of the following is a fruit? Check all that apply.</p>
            <choiceresponse>
              <checkboxgroup>
                <choice correct="true">apple
                  <choicehint selected="true">You are correct that an apple is a fruit because it is the fertilized
                  ovary that comes from an apple tree and contains seeds.</choicehint>
                  <choicehint selected="false">Remember that an apple is also a fruit.</choicehint></choice>
                <choice correct="true">pumpkin
                  <choicehint selected="true">You are correct that a pumpkin is a fruit because it is the fertilized
                  ovary of a squash plant and contains seeds.</choicehint>
                  <choicehint selected="false">Remember that a pumpkin is also a fruit.</choicehint></choice>
                <choice correct="false">potato
                  <choicehint selected="true">A potato is a vegetable, not a fruit, because it does not come from a
                  flower and does not contain seeds.</choicehint>
                  <choicehint selected="false">You are correct that a potato is a vegetable because it is an edible
                  part of a plant in tuber form.</choicehint></choice>
                <choice correct="true">tomato
                  <choicehint selected="true">You are correct that a tomato is a fruit because it is the fertilized
                  ovary of a tomato plant and contains seeds.</choicehint>
                  <choicehint selected="false">Many people mistakenly think a tomato is a vegetable. However, because
                  a tomato is the fertilized ovary of a tomato plant and contains seeds, it is a fruit.</choicehint>
                  </choice>
                <compoundhint value="A B D">An apple, pumpkin, and tomato are all fruits as they all are fertilized
                ovaries of a plant and contain seeds.</compoundhint>
                <compoundhint value="A B C D">You are correct that an apple, pumpkin, and tomato are all fruits as they
                all are fertilized ovaries of a plant and contain seeds. However, a potato is not a fruit as it is an
                edible part of a plant in tuber form and is a vegetable.</compoundhint>
              </checkboxgroup>
            </choiceresponse>


            <demandhint>
              <hint>A fruit is the fertilized ovary from a flower.</hint>
              <hint>A fruit contains seeds of the plant.</hint>
            </demandhint>
        </problem>
    """)

    sample_dropdown_with_hints_and_feedback_problem_xml = textwrap.dedent("""
        <problem>
            <p>You can provide feedback for each available option in a dropdown problem.</p>

            <p>You can also add hints for learners.</p>

            <p>Be sure to select Settings to specify a Display Name and other values that apply.</p>

            <p>Use the following example problem as a model.</p>

            <p> A/an ________ is a vegetable.</p>
            <optionresponse>
              <optioninput>
                <option correct="False">apple <optionhint>An apple is the fertilized ovary that comes from an apple
                tree and contains seeds, meaning it is a fruit.</optionhint></option>
                <option correct="False">pumpkin <optionhint>A pumpkin is the fertilized ovary of a squash plant and
                contains seeds, meaning it is a fruit.</optionhint></option>
                <option correct="True">potato <optionhint>A potato is an edible part of a plant in tuber form and is a
                vegetable.</optionhint></option>
                <option correct="False">tomato <optionhint>Many people mistakenly think a tomato is a vegetable.
                However, because a tomato is the fertilized ovary of a tomato plant and contains seeds, it is a fruit.
                </optionhint></option>
              </optioninput>
            </optionresponse>

            <demandhint>
              <hint>A fruit is the fertilized ovary from a flower.</hint>
              <hint>A fruit contains seeds of the plant.</hint>
            </demandhint>
        </problem>
    """)

    sample_multichoice_with_hints_and_feedback_problem_xml = textwrap.dedent("""
        <problem>
            <p>You can provide feedback for each option in a multiple choice problem.</p>

            <p>You can also add hints for learners.</p>

            <p>Be sure to select Settings to specify a Display Name and other values that apply.</p>

            <p>Use the following example problem as a model.</p>

            <p>Which of the following is a vegetable?</p>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice">
                <choice correct="false">apple <choicehint>An apple is the fertilized ovary that comes from an apple
                tree and contains seeds, meaning it is a fruit.</choicehint></choice>
                <choice correct="false">pumpkin <choicehint>A pumpkin is the fertilized ovary of a squash plant and
                contains seeds, meaning it is a fruit.</choicehint></choice>
                <choice correct="true">potato <choicehint>A potato is an edible part of a plant in tuber form and is a
                vegetable.</choicehint></choice>
                <choice correct="false">tomato <choicehint>Many people mistakenly think a tomato is a vegetable.
                However, because a tomato is the fertilized ovary of a tomato plant and contains seeds, it is a fruit.
                </choicehint></choice>
              </choicegroup>
            </multiplechoiceresponse>


            <demandhint>
              <hint>A fruit is the fertilized ovary from a flower.</hint>
              <hint>A fruit contains seeds of the plant.</hint>
            </demandhint>
        </problem>
    """)

    sample_numerical_input_with_hints_and_feedback_problem_xml = textwrap.dedent("""
        <problem>
            <p>You can provide feedback for correct answers in numerical input problems. You cannot provide feedback
            for incorrect answers.</p>

            <p>Use feedback for the correct answer to reinforce the process for arriving at the numerical value.</p>

            <p>You can also add hints for learners.</p>

            <p>Be sure to select Settings to specify a Display Name and other values that apply.</p>

            <p>Use the following example problem as a model.</p>

            <p>What is the arithmetic mean for the following set of numbers? (1, 5, 6, 3, 5)</p>

            <numericalresponse answer="4">
              <formulaequationinput/>
              <correcthint>The mean for this set of numbers is 20 / 5, which equals 4.</correcthint>
            </numericalresponse>
            <solution>
            <div class="detailed-solution">
            <p>Explanation</p>

            <p>The mean is calculated by summing the set of numbers and dividing by n. In this case:
            (1 + 5 + 6 + 3 + 5) / 5 = 20 / 5 = 4.</p>

            </div>
            </solution>

            <demandhint>
              <hint>The mean is calculated by summing the set of numbers and dividing by n.</hint>
              <hint>n is the count of items in the set.</hint>
            </demandhint>
        </problem>
    """)

    sample_text_input_with_hints_and_feedback_problem_xml = textwrap.dedent("""
        <problem>
            <p>You can provide feedback for the correct answer in text input problems, as well as for specific
            incorrect answers.</p>

            <p>Use feedback on expected incorrect answers to address common misconceptions and to provide guidance on
            how to arrive at the correct answer.</p>

            <p>Be sure to select Settings to specify a Display Name and other values that apply.</p>

            <p>Use the following example problem as a model.</p>

            <p>Which U.S. state has the largest land area?</p>

            <stringresponse answer="Alaska" type="ci" >
              <correcthint>Alaska is 576,400 square miles, more than double the land area of the second largest state,
              Texas.</correcthint>
              <stringequalhint answer="Texas">While many people think Texas is the largest state, it is actually the
              second largest, with 261,797 square miles.</stringequalhint>
              <stringequalhint answer="California">California is the third largest state, with 155,959 square miles.
              </stringequalhint>
              <textline size="20"/>
            </stringresponse>

            <demandhint>
              <hint>Consider the square miles, not population.</hint>
              <hint>Consider all 50 states, not just the continental United States.</hint>
            </demandhint>
        </problem>
    """)

    def _create_descriptor(self, xml, name=None):
        """ Creates a ProblemBlock to run test against """
        descriptor = CapaFactory.create()
        descriptor.data = xml
        if name:
            descriptor.display_name = name
        return descriptor

    @ddt.data(*sorted(responsetypes.registry.registered_tags()))
    def test_all_response_types(self, response_tag):
        """ Tests that every registered response tag is correctly returned """
        xml = "<problem><{response_tag}></{response_tag}></problem>".format(response_tag=response_tag)
        name = "Some Capa Problem"
        descriptor = self._create_descriptor(xml, name=name)
        assert descriptor.problem_types == {response_tag}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': [response_tag],
                'content': {'display_name': name, 'capa_content': ''}}

    def test_response_types_ignores_non_response_tags(self):
        xml = textwrap.dedent("""
            <problem>
            <p>Label</p>
            <div>Some comment</div>
            <multiplechoiceresponse>
              <choicegroup type="MultipleChoice" answer-pool="4">
                <choice correct="false">Apple</choice>
                <choice correct="false">Banana</choice>
                <choice correct="false">Chocolate</choice>
                <choice correct ="true">Donut</choice>
              </choicegroup>
            </multiplechoiceresponse>
            </problem>
        """)
        name = "Test Capa Problem"
        descriptor = self._create_descriptor(xml, name=name)
        assert descriptor.problem_types == {'multiplechoiceresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['multiplechoiceresponse'],
                'content': {'display_name': name, 'capa_content': ' Label Some comment Apple Banana Chocolate Donut '}}

    def test_response_types_multiple_tags(self):
        xml = textwrap.dedent("""
            <problem>
                <p>Label</p>
                <div>Some comment</div>
                <multiplechoiceresponse>
                  <choicegroup type="MultipleChoice" answer-pool="1">
                    <choice correct ="true">Donut</choice>
                  </choicegroup>
                </multiplechoiceresponse>
                <multiplechoiceresponse>
                  <choicegroup type="MultipleChoice" answer-pool="1">
                    <choice correct ="true">Buggy</choice>
                  </choicegroup>
                </multiplechoiceresponse>
                <optionresponse>
                    <optioninput options="('1','2')" correct="2"></optioninput>
                </optionresponse>
            </problem>
        """)
        name = "Other Test Capa Problem"
        descriptor = self._create_descriptor(xml, name=name)
        assert descriptor.problem_types == {'multiplechoiceresponse', 'optionresponse'}

        # We are converting problem_types to a set to compare it later without taking into account the order
        # the reasoning behind is that the problem_types (property) is represented by dict and when it is converted
        # to list its ordering is different everytime.

        indexing_result = descriptor.index_dictionary()
        indexing_result['problem_types'] = set(indexing_result['problem_types'])
        self.assertDictEqual(
            indexing_result, {
                'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': {"optionresponse", "multiplechoiceresponse"},
                'content': {
                    'display_name': name,
                    'capa_content': " Label Some comment Donut Buggy '1','2' "
                },
            }
        )

    def test_solutions_not_indexed(self):
        xml = textwrap.dedent("""
            <problem>
                <solution>Test solution.</solution>
                <solution explanation-id="solution0">Test solution with attribute.</solution>
                <solutionset>
                    Test solutionset.
                    <solution explanation-id="solution1">Test solution within solutionset.</solution>
                </solutionset>

                <targetedfeedback>Test feedback.</targetedfeedback>
                <targetedfeedback explanation-id="feedback0">Test feedback with attribute.</targetedfeedback>
                <targetedfeedbackset>
                    Test FeedbackSet.
                    <targetedfeedback explanation-id="feedback1">Test feedback within feedbackset.</targetedfeedback>
                </targetedfeedbackset>

                <answer>Test answer.</answer>
                <answer type="loncapa/python">Test answer with attribute.</answer>

                <script>Test script.</script>
                <script type="loncapa/python">Test script with attribute.</script>

                <style>Test style.</style>
                <style media="all and (max-width: 1920px)">Test style with attribute.</style>

                <choicehint>Test choicehint.</choicehint>
                <hint>Test hint.</hint>
                <hintpart>Test hintpart.</hintpart>
            </problem>
        """)
        name = "Blank Common Capa Problem"
        descriptor = self._create_descriptor(xml, name=name)
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': [],
                'content': {'display_name': name, 'capa_content': ' '}}

    def test_indexing_checkboxes(self):
        name = "Checkboxes"
        descriptor = self._create_descriptor(self.sample_checkbox_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            Title
            Description
            Example
            The following languages are in the Indo-European family:
            Urdu
            Finnish
            Marathi
            French
            Hungarian
            Note: Make sure you select all of the correct options—there may be more than one!
        """)
        assert descriptor.problem_types == {'choiceresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['choiceresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_dropdown(self):
        name = "Dropdown"
        descriptor = self._create_descriptor(self.sample_dropdown_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            Dropdown problems allow learners to select only one option from a list of options.
            Description
            You can use the following example problem as a model.
            Which of the following countries celebrates its independence on August 15? 'India','Spain','China','Bermuda'
        """)
        assert descriptor.problem_types == {'optionresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['optionresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_multiple_choice(self):
        name = "Multiple Choice"
        descriptor = self._create_descriptor(self.sample_multichoice_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            Multiple choice problems allow learners to select only one option.
            When you add the problem, be sure to select Settings to specify a Display Name and other values.
            You can use the following example problem as a model.
            Which of the following countries has the largest population?
            Brazil
            Germany
            Indonesia
            Russia
        """)
        assert descriptor.problem_types == {'multiplechoiceresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['multiplechoiceresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_numerical_input(self):
        name = "Numerical Input"
        descriptor = self._create_descriptor(self.sample_numerical_input_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            In a numerical input problem, learners enter numbers or a specific and relatively simple mathematical
            expression. Learners enter the response in plain text, and the system then converts the text to a symbolic
            expression that learners can see below the response field.
            The system can handle several types of characters, including basic operators, fractions, exponents, and
            common constants such as "i". You can refer learners to "Entering Mathematical and Scientific Expressions"
            in the edX Guide for Students for more information.
            When you add the problem, be sure to select Settings to specify a Display Name and other values that
            apply.
            You can use the following example problems as models.
            How many miles away from Earth is the sun? Use scientific notation to answer.
            The square of what number is -100?
        """)
        assert descriptor.problem_types == {'numericalresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['numericalresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_text_input(self):
        name = "Text Input"
        descriptor = self._create_descriptor(self.sample_text_input_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            In text input problems, also known as "fill-in-the-blank" problems, learners enter text into a response
            field. The text can include letters and characters such as punctuation marks. The text that the learner
            enters must match your specified answer text exactly. You can specify more than one correct answer.
            Learners must enter a response that matches one of the correct answers exactly.
            When you add the problem, be sure to select Settings to specify a Display Name and other values that
            apply.
            You can use the following example problem as a model.
            What was the first post-secondary school in China to allow both male and female students?
        """)
        assert descriptor.problem_types == {'stringresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['stringresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_non_latin_problem(self):
        sample_text_input_problem_xml = textwrap.dedent("""
            <problem>
                <script type="text/python">FX1_VAL='Καλημέρα'</script>
                <p>Δοκιμή με μεταβλητές με Ελληνικούς χαρακτήρες μέσα σε python: $FX1_VAL</p>
            </problem>
        """)
        name = "Non latin Input"
        descriptor = self._create_descriptor(sample_text_input_problem_xml, name=name)
        capa_content = " Δοκιμή με μεταβλητές με Ελληνικούς χαρακτήρες μέσα σε python: $FX1_VAL "

        descriptor_dict = descriptor.index_dictionary()
        assert descriptor_dict['content']['capa_content'] == smart_str(capa_content)

    def test_indexing_checkboxes_with_hints_and_feedback(self):
        name = "Checkboxes with Hints and Feedback"
        descriptor = self._create_descriptor(self.sample_checkboxes_with_hints_and_feedback_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            You can provide feedback for each option in a checkbox problem, with distinct feedback depending on
            whether or not the learner selects that option.
            You can also provide compound feedback for a specific combination of answers. For example, if you have
            three possible answers in the problem, you can configure specific feedback for when a learner selects each
            combination of possible answers.
            You can also add hints for learners.
            Be sure to select Settings to specify a Display Name and other values that apply.
            Use the following example problem as a model.
            Which of the following is a fruit? Check all that apply.
            apple
            pumpkin
            potato
            tomato
        """)
        assert descriptor.problem_types == {'choiceresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['choiceresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_dropdown_with_hints_and_feedback(self):
        name = "Dropdown with Hints and Feedback"
        descriptor = self._create_descriptor(self.sample_dropdown_with_hints_and_feedback_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            You can provide feedback for each available option in a dropdown problem.
            You can also add hints for learners.
            Be sure to select Settings to specify a Display Name and other values that apply.
            Use the following example problem as a model.
            A/an ________ is a vegetable.
            apple
            pumpkin
            potato
            tomato
        """)
        assert descriptor.problem_types == {'optionresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['optionresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_multiple_choice_with_hints_and_feedback(self):
        name = "Multiple Choice with Hints and Feedback"
        descriptor = self._create_descriptor(self.sample_multichoice_with_hints_and_feedback_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            You can provide feedback for each option in a multiple choice problem.
            You can also add hints for learners.
            Be sure to select Settings to specify a Display Name and other values that apply.
            Use the following example problem as a model.
            Which of the following is a vegetable?
            apple
            pumpkin
            potato
            tomato
        """)
        assert descriptor.problem_types == {'multiplechoiceresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['multiplechoiceresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_numerical_input_with_hints_and_feedback(self):
        name = "Numerical Input with Hints and Feedback"
        descriptor = self._create_descriptor(self.sample_numerical_input_with_hints_and_feedback_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            You can provide feedback for correct answers in numerical input problems. You cannot provide feedback
            for incorrect answers.
            Use feedback for the correct answer to reinforce the process for arriving at the numerical value.
            You can also add hints for learners.
            Be sure to select Settings to specify a Display Name and other values that apply.
            Use the following example problem as a model.
            What is the arithmetic mean for the following set of numbers? (1, 5, 6, 3, 5)
        """)
        assert descriptor.problem_types == {'numericalresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['numericalresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_text_input_with_hints_and_feedback(self):
        name = "Text Input with Hints and Feedback"
        descriptor = self._create_descriptor(self.sample_text_input_with_hints_and_feedback_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            You can provide feedback for the correct answer in text input problems, as well as for specific
            incorrect answers.
            Use feedback on expected incorrect answers to address common misconceptions and to provide guidance on
            how to arrive at the correct answer.
            Be sure to select Settings to specify a Display Name and other values that apply.
            Use the following example problem as a model.
            Which U.S. state has the largest land area?
        """)
        assert descriptor.problem_types == {'stringresponse'}
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': ['stringresponse'],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_indexing_problem_with_html_tags(self):
        sample_problem_xml = textwrap.dedent("""
            <problem>
                <style>p {left: 10px;}</style>
                <!-- Beginning of the html -->
                <p>This has HTML comment in it.<!-- Commenting Content --></p>
                <!-- Here comes CDATA -->
                <![CDATA[This is just a CDATA!]]>
                <p>HTML end.</p>
                <!-- Script that makes everything alive! -->
                <script>
                    var alive;
                </script>
            </problem>
        """)
        name = "Mixed business"
        descriptor = self._create_descriptor(sample_problem_xml, name=name)
        capa_content = textwrap.dedent("""
            This has HTML comment in it.
            HTML end.
        """)
        assert descriptor.index_dictionary() ==\
               {'content_type': ProblemBlock.INDEX_CONTENT_TYPE,
                'problem_types': [],
                'content': {'display_name': name, 'capa_content': capa_content.replace('\n', ' ')}}

    def test_invalid_xml_handling(self):
        """
        Tests to confirm that invalid XML throws errors during xblock creation,
        so as not to allow bad data into modulestore.
        """
        sample_invalid_xml = textwrap.dedent("""
            <problem>
            </proble-oh no my finger broke and I can't close the problem tag properly...
        """)
        with pytest.raises(etree.XMLSyntaxError):
            self._create_descriptor(sample_invalid_xml, name="Invalid XML")

    def test_invalid_dropdown_xml(self):
        """
        Verify the capa problem cannot be created from dropdown xml with multiple correct answers.
        """
        problem_xml = textwrap.dedent("""
        <problem>
            <optionresponse>
              <p>You can use this template as a guide to the simple editor markdown and OLX markup to use for dropdown
               problems. Edit this component to replace this template with your own assessment.</p>
            <label>Add the question text, or prompt, here. This text is required.</label>
            <description>You can add an optional tip or note related to the prompt like this. </description>
            <optioninput>
                <option correct="False">an incorrect answer</option>
                <option correct="True">the correct answer</option>
                <option correct="True">an incorrect answer</option>
              </optioninput>
            </optionresponse>
        </problem>
        """)
        with pytest.raises(Exception):
            CapaFactory.create(xml=problem_xml)


class ComplexEncoderTest(unittest.TestCase):  # lint-amnesty, pylint: disable=missing-class-docstring

    def test_default(self):
        """
        Check that complex numbers can be encoded into JSON.
        """
        complex_num = 1 - 1j
        expected_str = '1-1*j'
        json_str = json.dumps(complex_num, cls=ComplexEncoder)
        assert expected_str == json_str[1:(- 1)]
        # ignore quotes


class ProblemCheckTrackingTest(unittest.TestCase):
    """
    Ensure correct tracking information is included in events emitted during problem checks.
    """

    def setUp(self):
        super().setUp()
        self.maxDiff = None

    def test_choice_answer_text(self):
        xml = """\
            <problem display_name="Multiple Choice Questions">
              <optionresponse>
                <label>What color is the open ocean on a sunny day?</label>
                <optioninput options="('yellow','blue','green')" correct="blue"/>
              </optionresponse>

              <multiplechoiceresponse>
                <label>Which piece of furniture is built for sitting?</label>
                <choicegroup type="MultipleChoice">
                  <choice correct="false"><text>a table</text></choice>
                  <choice correct="false"><text>a desk</text></choice>
                  <choice correct="true"><text>a chair</text></choice>
                  <choice correct="false"><text>a bookshelf</text></choice>
                </choicegroup>
              </multiplechoiceresponse>

              <choiceresponse>
                <label>Which of the following are musical instruments?</label>
                <checkboxgroup>
                  <choice correct="true">a piano</choice>
                  <choice correct="false">a tree</choice>
                  <choice correct="true">a guitar</choice>
                  <choice correct="false">a window</choice>
                </checkboxgroup>
              </choiceresponse>
            </problem>
            """

        # Whitespace screws up comparisons
        xml = ''.join(line.strip() for line in xml.split('\n'))
        factory = self.capa_factory_for_problem_xml(xml)
        module = factory.create()

        answer_input_dict = {
            factory.input_key(2): 'blue',
            factory.input_key(3): 'choice_0',
            factory.input_key(4): ['choice_0', 'choice_1'],
        }
        event = self.get_event_for_answers(module, answer_input_dict)

        assert event['submission'] ==\
               {factory.answer_key(2): {'question': 'What color is the open ocean on a sunny day?',
                                        'answer': 'blue', 'response_type': 'optionresponse',
                                        'input_type': 'optioninput',
                                        'correct': True,
                                        'group_label': '',
                                        'variant': ''},
                factory.answer_key(3): {'question': 'Which piece of furniture is built for sitting?',
                                        'answer': '<text>a table</text>',
                                        'response_type': 'multiplechoiceresponse',
                                        'input_type': 'choicegroup',
                                        'correct': False,
                                        'group_label': '',
                                        'variant': ''},
                factory.answer_key(4): {'question': 'Which of the following are musical instruments?',
                                        'answer': ['a piano', 'a tree'],
                                        'response_type': 'choiceresponse',
                                        'input_type': 'checkboxgroup',
                                        'correct': False,
                                        'group_label': '',
                                        'variant': ''}}

    def capa_factory_for_problem_xml(self, xml):  # lint-amnesty, pylint: disable=missing-function-docstring
        class CustomCapaFactory(CapaFactory):
            """
            A factory for creating a Capa problem with arbitrary xml.
            """
            sample_problem_xml = textwrap.dedent(xml)

        return CustomCapaFactory

    def get_event_for_answers(self, module, answer_input_dict):  # lint-amnesty, pylint: disable=missing-function-docstring
        with patch.object(module.runtime, 'publish') as mock_track_function:
            module.submit_problem(answer_input_dict)

            assert len(mock_track_function.mock_calls) >= 2
            # There are potentially 2 track logs: answers and hint. [-1]=answers.
            mock_call = mock_track_function.mock_calls[-1]
            event = mock_call[1][2]

            return event

    def test_numerical_textline(self):
        factory = CapaFactory
        module = factory.create()

        answer_input_dict = {
            factory.input_key(2): '3.14'
        }

        event = self.get_event_for_answers(module, answer_input_dict)
        assert event['submission'] ==\
               {factory.answer_key(2): {'question': '', 'answer': '3.14',
                                        'response_type': 'numericalresponse',
                                        'input_type': 'textline',
                                        'correct': True,
                                        'group_label': '',
                                        'variant': ''}}

    def test_multiple_inputs(self):
        group_label = 'Choose the correct color'
        input1_label = 'What color is the sky?'
        input2_label = 'What color are pine needles?'
        factory = self.capa_factory_for_problem_xml("""\
            <problem display_name="Multiple Inputs">
              <optionresponse>
                <label>{}</label>
                <optioninput options="('yellow','blue','green')" correct="blue" label="{}"/>
                <optioninput options="('yellow','blue','green')" correct="green" label="{}"/>
              </optionresponse>
            </problem>
            """.format(group_label, input1_label, input2_label))
        module = factory.create()
        answer_input_dict = {
            factory.input_key(2, 1): 'blue',
            factory.input_key(2, 2): 'yellow',
        }

        event = self.get_event_for_answers(module, answer_input_dict)
        assert event['submission'] ==\
               {factory.answer_key(2, 1): {'group_label': group_label,
                                           'question': input1_label,
                                           'answer': 'blue',
                                           'response_type': 'optionresponse',
                                           'input_type': 'optioninput',
                                           'correct': True, 'variant': ''},
                factory.answer_key(2, 2): {'group_label': group_label,
                                           'question': input2_label,
                                           'answer': 'yellow',
                                           'response_type': 'optionresponse',
                                           'input_type': 'optioninput',
                                           'correct': False, 'variant': ''}}

    def test_optioninput_extended_xml(self):
        """Test the new XML form of writing with <option> tag instead of options= attribute."""
        group_label = 'Are you the Gatekeeper?'
        input1_label = 'input 1 label'
        input2_label = 'input 2 label'
        factory = self.capa_factory_for_problem_xml("""\
            <problem display_name="Woo Hoo">
                <optionresponse>
                   <label>{}</label>
                   <optioninput label="{}">
                       <option correct="True" label="Good Job">
                           apple
                           <optionhint>
                               banana
                           </optionhint>
                       </option>
                       <option correct="False" label="blorp">
                           cucumber
                           <optionhint>
                               donut
                           </optionhint>
                       </option>
                   </optioninput>

                   <optioninput label="{}">
                       <option correct="True">
                           apple
                           <optionhint>
                               banana
                           </optionhint>
                       </option>
                       <option correct="False">
                           cucumber
                           <optionhint>
                               donut
                           </optionhint>
                       </option>
                   </optioninput>
                 </optionresponse>
            </problem>
            """.format(group_label, input1_label, input2_label))
        module = factory.create()

        answer_input_dict = {
            factory.input_key(2, 1): 'apple',
            factory.input_key(2, 2): 'cucumber',
        }

        event = self.get_event_for_answers(module, answer_input_dict)
        assert event['submission'] ==\
               {factory.answer_key(2, 1): {'group_label': group_label,
                                           'question': input1_label,
                                           'answer': 'apple',
                                           'response_type': 'optionresponse',
                                           'input_type': 'optioninput',
                                           'correct': True, 'variant': ''},
                factory.answer_key(2, 2): {'group_label': group_label,
                                           'question': input2_label,
                                           'answer': 'cucumber',
                                           'response_type': 'optionresponse',
                                           'input_type': 'optioninput',
                                           'correct': False, 'variant': ''}}

    def test_rerandomized_inputs(self):
        factory = CapaFactory
        module = factory.create(rerandomize=RANDOMIZATION.ALWAYS)

        answer_input_dict = {
            factory.input_key(2): '3.14'
        }

        event = self.get_event_for_answers(module, answer_input_dict)
        assert event['submission'] ==\
               {factory.answer_key(2): {'question': '',
                                        'answer': '3.14',
                                        'response_type': 'numericalresponse',
                                        'input_type': 'textline',
                                        'correct': True,
                                        'group_label': '',
                                        'variant': module.seed}}

    @patch.object(XQueueInterface, '_http_post')
    def test_file_inputs(self, mock_xqueue_post):
        fnames = ["prog1.py", "prog2.py", "prog3.py"]
        fpaths = [os.path.join(DATA_DIR, "capa", fname) for fname in fnames]
        fileobjs = [open(fpath) for fpath in fpaths]
        for fileobj in fileobjs:
            self.addCleanup(fileobj.close)

        factory = CapaFactoryWithFiles
        module = factory.create()

        # Mock the XQueueInterface post method
        mock_xqueue_post.return_value = (0, "ok")

        answer_input_dict = {
            CapaFactoryWithFiles.input_key(response_num=2): fileobjs,
            CapaFactoryWithFiles.input_key(response_num=3): 'None',
        }

        event = self.get_event_for_answers(module, answer_input_dict)
        assert event['submission'] ==\
               {factory.answer_key(2): {'question': '',
                                        'answer': fpaths,
                                        'response_type': 'coderesponse',
                                        'input_type': 'filesubmission',
                                        'correct': False,
                                        'group_label': '',
                                        'variant': ''},
                factory.answer_key(3): {'answer': 'None',
                                        'correct': True,
                                        'group_label': '',
                                        'question': '',
                                        'response_type': 'customresponse',
                                        'input_type': 'textline',
                                        'variant': ''}}

    def test_get_answer_with_jump_to_id_urls(self):
        """
        Make sure replace_jump_to_id_urls() is called in get_answer.
        """
        problem_xml = textwrap.dedent("""
        <problem>
            <p>What is 1+4?</p>
                <numericalresponse answer="5">
                  <formulaequationinput />
                </numericalresponse>

                <solution>
                <div class="detailed-solution">
                <p>Explanation</p>
                <a href="/jump_to_id/c0f8d54964bc44a4a1deb8ecce561ecd">here's the same link to the hint page.</a>
                </div>
                </solution>
        </problem>
        """)

        data = {}
        problem = CapaFactory.create(showanswer='always', xml=problem_xml)
        problem.runtime.service(problem, 'replace_urls').replace_urls = Mock()

        problem.get_answer(data)
        assert problem.runtime.service(problem, 'replace_urls').replace_urls.called


class ProblemBlockReportGenerationTest(unittest.TestCase):
    """
    Ensure that Capa report generation works correctly
    """

    def setUp(self):  # lint-amnesty, pylint: disable=super-method-not-called
        self.find_question_label_patcher = patch(
            'xmodule.capa.capa_problem.LoncapaProblem.find_question_label',
            lambda self, answer_id: answer_id
        )
        self.find_answer_text_patcher = patch(
            'xmodule.capa.capa_problem.LoncapaProblem.find_answer_text',
            lambda self, answer_id, current_answer: current_answer
        )
        self.find_question_label_patcher.start()
        self.find_answer_text_patcher.start()
        self.addCleanup(self.find_question_label_patcher.stop)
        self.addCleanup(self.find_answer_text_patcher.stop)

    def _mock_user_state_generator(self, user_count=1, response_count=10):
        for uid in range(user_count):
            yield self._user_state(username=f'user{uid}', response_count=response_count)

    def _user_state(self, username='testuser', response_count=10, suffix=''):
        return XBlockUserState(
            username=username,
            state={
                'student_answers': {
                    f'{username}_answerid_{aid}{suffix}': f'{username}_answer_{aid}'
                    for aid in range(response_count)
                },
                'seed': 1,
                'correct_map': {},
            },
            block_key=None,
            updated=None,
            scope=None,
        )

    def _get_descriptor(self):  # lint-amnesty, pylint: disable=missing-function-docstring
        scope_ids = Mock(block_type='problem')
        descriptor = ProblemBlock(get_test_system(), scope_ids=scope_ids)
        descriptor.runtime = Mock()
        descriptor.data = '<problem/>'
        return descriptor

    def test_generate_report_data_not_implemented(self):
        scope_ids = Mock(block_type='noproblem')
        descriptor = ProblemBlock(get_test_system(), scope_ids=scope_ids)
        with pytest.raises(NotImplementedError):
            next(descriptor.generate_report_data(iter([])))

    def test_generate_report_data_limit_responses(self):
        descriptor = self._get_descriptor()
        report_data = list(descriptor.generate_report_data(self._mock_user_state_generator(), 2))
        assert 2 == len(report_data)

    def test_generate_report_data_dont_limit_responses(self):
        descriptor = self._get_descriptor()
        user_count = 5
        response_count = 10
        report_data = list(descriptor.generate_report_data(
            self._mock_user_state_generator(
                user_count=user_count,
                response_count=response_count,
            )
        ))
        assert (user_count * response_count) == len(report_data)

    def test_generate_report_data_skip_dynamath(self):
        descriptor = self._get_descriptor()
        iterator = iter([self._user_state(suffix='_dynamath')])
        report_data = list(descriptor.generate_report_data(iterator))
        assert 0 == len(report_data)

    def test_generate_report_data_report_loncapa_error(self):
        #Test to make sure reports continue despite loncappa errors, and write them into the report.
        descriptor = self._get_descriptor()
        with patch('xmodule.capa_module.LoncapaProblem') as mock_LoncapaProblem:
            mock_LoncapaProblem.side_effect = LoncapaProblemError
            report_data = list(descriptor.generate_report_data(
                self._mock_user_state_generator(
                    user_count=1,
                    response_count=5,
                )
            ))
            assert 'Python Error: No Answer Retrieved' in list(report_data[0][1].values())
