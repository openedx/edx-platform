# -*- coding: utf-8 -*-
"""
Tests of extended hints
"""


import unittest

from ddt import ddt, data, unpack

# With the use of ddt, some of the data expected_string cases below are naturally long stretches
# of text text without whitespace. I think it's best to leave such lines intact
# in the test code. Therefore:
# pylint: disable=line-too-long
# For out many ddt data cases, prefer a compact form of { .. }

from . import new_loncapa_problem, load_fixture


class HintTest(unittest.TestCase):
    """Base class for tests of extended hinting functionality."""

    def correctness(self, problem_id, choice):
        """Grades the problem and returns the 'correctness' string from cmap."""
        student_answers = {problem_id: choice}
        cmap = self.problem.grade_answers(answers=student_answers)    # pylint: disable=no-member
        return cmap[problem_id]['correctness']

    def get_hint(self, problem_id, choice):
        """Grades the problem and returns its hint from cmap or the empty string."""
        student_answers = {problem_id: choice}
        cmap = self.problem.grade_answers(answers=student_answers)    # pylint: disable=no-member
        adict = cmap.cmap.get(problem_id)
        if adict:
            return adict['msg']
        else:
            return ''


# It is a little surprising how much more complicated TextInput is than all the other cases.
@ddt
class TextInputHintsTest(HintTest):
    """
    Test Text Input Hints Test
    """
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    def test_tracking_log(self):
        """Test that the tracking log comes out right."""
        self.problem.capa_module.reset_mock()
        self.get_hint(u'1_3_1', u'Blue')
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'module_id': 'i4x://Foo/bar/mock/abc',
             'problem_part_id': '1_2',
             'trigger_type': 'single',
             'hint_label': u'<span class="icon fa fa-check" aria-hidden="true"></span>Correct',
             'correctness': True,
             'student_answer': [u'Blue'],
             'question_type': 'stringresponse',
             'hints': [{'text': 'The red light is scattered by water molecules leaving only blue light.'}]}
        )

    @data(
        {'problem_id': u'1_2_1', u'choice': u'GermanyΩ',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">I do not think so.&#937;</div></div>'},
        {'problem_id': u'1_2_1', u'choice': u'franceΩ',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Viva la France!&#937;</div></div>'},
        {'problem_id': u'1_2_1', u'choice': u'FranceΩ',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Viva la France!&#937;</div></div>'},
        {'problem_id': u'1_2_1', u'choice': u'Mexico',
         'expected_string': ''},
        {'problem_id': u'1_2_1', u'choice': u'USAΩ',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Less well known, but yes, there is a Paris, Texas.&#937;</div></div>'},
        {'problem_id': u'1_2_1', u'choice': u'usaΩ',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Less well known, but yes, there is a Paris, Texas.&#937;</div></div>'},
        {'problem_id': u'1_2_1', u'choice': u'uSAxΩ',
         'expected_string': u''},
        {'problem_id': u'1_2_1', u'choice': u'NICKLANDΩ',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">The country name does not end in LAND&#937;</div></div>'},
        {'problem_id': u'1_3_1', u'choice': u'Blue',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">The red light is scattered by water molecules leaving only blue light.</div></div>'},
        {'problem_id': u'1_3_1', u'choice': u'blue',
         'expected_string': u''},
        {'problem_id': u'1_3_1', u'choice': u'b',
         'expected_string': u''},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


@ddt
class TextInputExtendedHintsCaseInsensitive(HintTest):
    """Test Text Input Extended hints Case Insensitive"""
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_5_1', 'choice': 'abc', 'expected_string': ''},  # wrong answer yielding no hint
        {'problem_id': u'1_5_1', 'choice': 'A', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">Woo Hoo: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'a', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">Woo Hoo: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'B', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'b', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'C', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="hint-text">hint4</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'c', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="hint-text">hint4</div></div>'},
        # regexp cases
        {'problem_id': u'1_5_1', 'choice': 'FGGG', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="hint-text">hint6</div></div>'},
        {'problem_id': u'1_5_1', 'choice': 'fgG', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="hint-text">hint6</div></div>'},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


@ddt
class TextInputExtendedHintsCaseSensitive(HintTest):
    """Sometimes the semantics can be encoded in the class name."""
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_6_1', 'choice': 'abc', 'expected_string': ''},
        {'problem_id': u'1_6_1', 'choice': 'A', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_6_1', 'choice': 'a', 'expected_string': u''},
        {'problem_id': u'1_6_1', 'choice': 'B', 'expected_string':
         u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_6_1', 'choice': 'b', 'expected_string': u''},
        {'problem_id': u'1_6_1', 'choice': 'C', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint4</div></div>'},
        {'problem_id': u'1_6_1', 'choice': 'c', 'expected_string': u''},
        # regexp cases
        {'problem_id': u'1_6_1', 'choice': 'FGG', 'expected_string':
         u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint6</div></div>'},
        {'problem_id': u'1_6_1', 'choice': 'fgG', 'expected_string': u''},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, expected_string):
        message_text = self.get_hint(problem_id, choice)
        self.assertEqual(message_text, expected_string)


@ddt
class TextInputExtendedHintsCompatible(HintTest):
    """
    Compatibility test with mixed old and new style additional_answer tags.
    """
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_7_1', 'choice': 'A', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_7_1', 'choice': 'B', 'correct': 'correct', 'expected_string': ''},
        {'problem_id': u'1_7_1', 'choice': 'C', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_7_1', 'choice': 'D', 'correct': 'incorrect', 'expected_string': ''},
        # check going through conversion with difficult chars
        {'problem_id': u'1_7_1', 'choice': """<&"'>""", 'correct': 'correct', 'expected_string': ''},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, correct, expected_string):
        message_text = self.get_hint(problem_id, choice)
        self.assertEqual(message_text, expected_string)
        self.assertEqual(self.correctness(problem_id, choice), correct)


@ddt
class TextInputExtendedHintsRegex(HintTest):
    """
    Extended hints where the answer is regex mode.
    """
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_8_1', 'choice': 'ABwrong', 'correct': 'incorrect', 'expected_string': ''},
        {'problem_id': u'1_8_1', 'choice': 'ABC', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'ABBBBC', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'aBc', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint1</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'BBBB', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'bbb', 'correct': 'correct',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">hint2</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'C', 'correct': 'incorrect',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint4</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'c', 'correct': 'incorrect',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint4</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'D', 'correct': 'incorrect',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint6</div></div>'},
        {'problem_id': u'1_8_1', 'choice': 'd', 'correct': 'incorrect',
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">hint6</div></div>'},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, correct, expected_string):
        message_text = self.get_hint(problem_id, choice)
        self.assertEqual(message_text, expected_string)
        self.assertEqual(self.correctness(problem_id, choice), correct)


@ddt
class NumericInputHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the numeric input problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_numeric_input.xml')
    problem = new_loncapa_problem(xml)          # this problem is properly constructed

    def test_tracking_log(self):
        self.get_hint(u'1_2_1', u'1.141')
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'module_id': 'i4x://Foo/bar/mock/abc', 'problem_part_id': '1_1', 'trigger_type': 'single',
             'hint_label': u'Nice',
             'correctness': True,
             'student_answer': [u'1.141'],
             'question_type': 'numericalresponse',
             'hints': [{'text': 'The square root of two turns up in the strangest places.'}]}
        )

    @data(
        {'problem_id': u'1_2_1', 'choice': '1.141',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">Nice: </span><div class="hint-text">The square root of two turns up in the strangest places.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': '4',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Pretty easy, uh?.</div></div>'},
        # should get hint, when correct via numeric-tolerance
        {'problem_id': u'1_2_1', 'choice': '1.15',
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">Nice: </span><div class="hint-text">The square root of two turns up in the strangest places.</div></div>'},
        # when they answer wrong, nothing
        {'problem_id': u'1_2_1', 'choice': '2', 'expected_string': ''},
    )
    @unpack
    def test_numeric_input_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


@ddt
class CheckboxHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the checkbox problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_checkbox.xml')
    problem = new_loncapa_problem(xml)          # this problem is properly constructed

    @data(
        {'problem_id': u'1_2_1', 'choice': [u'choice_0'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">You are right that apple is a fruit.</div><div class="hint-text">You are right that mushrooms are not fruit</div><div class="hint-text">Remember that grape is also a fruit.</div><div class="hint-text">What is a camero anyway?</div></div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_1'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">Remember that apple is also a fruit.</div><div class="hint-text">Mushroom is a fungus, not a fruit.</div><div class="hint-text">Remember that grape is also a fruit.</div><div class="hint-text">What is a camero anyway?</div></div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_2'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">Remember that apple is also a fruit.</div><div class="hint-text">You are right that mushrooms are not fruit</div><div class="hint-text">You are right that grape is a fruit</div><div class="hint-text">What is a camero anyway?</div></div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_3'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">Remember that apple is also a fruit.</div><div class="hint-text">You are right that mushrooms are not fruit</div><div class="hint-text">Remember that grape is also a fruit.</div><div class="hint-text">What is a camero anyway?</div></div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_4'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">Remember that apple is also a fruit.</div><div class="hint-text">You are right that mushrooms are not fruit</div><div class="hint-text">Remember that grape is also a fruit.</div><div class="hint-text">I do not know what a Camero is but it is not a fruit.</div></div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_0', u'choice_1'],  # compound
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label">Almost right: </span><div class="hint-text">You are right that apple is a fruit, but there is one you are missing. Also, mushroom is not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_1', u'choice_2'],  # compound
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">You are right that grape is a fruit, but there is one you are missing. Also, mushroom is not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_0', u'choice_2'],
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="feedback-hint-multi"><div class="hint-text">You are right that apple is a fruit.</div><div class="hint-text">You are right that mushrooms are not fruit</div><div class="hint-text">You are right that grape is a fruit</div><div class="hint-text">What is a camero anyway?</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">No, sorry, a banana is a fruit.</div><div class="hint-text">You are right that mushrooms are not vegatbles</div><div class="hint-text">Brussel sprout is the only vegetable in this list.</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_1'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">poor banana.</div><div class="hint-text">You are right that mushrooms are not vegatbles</div><div class="hint-text">Brussel sprout is the only vegetable in this list.</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_2'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">poor banana.</div><div class="hint-text">Mushroom is a fungus, not a vegetable.</div><div class="hint-text">Brussel sprout is the only vegetable in this list.</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_3'],
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="feedback-hint-multi"><div class="hint-text">poor banana.</div><div class="hint-text">You are right that mushrooms are not vegatbles</div><div class="hint-text">Brussel sprouts are vegetables.</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0', u'choice_1'],  # compound
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label">Very funny: </span><div class="hint-text">Making a banana split?</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_1', u'choice_2'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">poor banana.</div><div class="hint-text">Mushroom is a fungus, not a vegetable.</div><div class="hint-text">Brussel sprout is the only vegetable in this list.</div></div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0', u'choice_2'],
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">No, sorry, a banana is a fruit.</div><div class="hint-text">Mushroom is a fungus, not a vegetable.</div><div class="hint-text">Brussel sprout is the only vegetable in this list.</div></div></div>'},

        # check for interaction between compoundhint and correct/incorrect
        {'problem_id': u'1_4_1', 'choice': [u'choice_0', u'choice_1'],  # compound
         'expected_string': u'<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">AB</div></div>'},
        {'problem_id': u'1_4_1', 'choice': [u'choice_0', u'choice_2'],  # compound
         'expected_string': u'<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">AC</div></div>'},

        # check for labeling where multiple child hints have labels
        # These are some tricky cases
        {'problem_id': '1_5_1', 'choice': ['choice_0', 'choice_1'],
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">AA: </span><div class="feedback-hint-multi"><div class="hint-text">aa</div></div></div>'},
        {'problem_id': '1_5_1', 'choice': ['choice_0'],
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">aa</div><div class="hint-text">bb</div></div></div>'},
        {'problem_id': '1_5_1', 'choice': ['choice_1'],
         'expected_string': ''},
        {'problem_id': '1_5_1', 'choice': [],
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label">BB: </span><div class="feedback-hint-multi"><div class="hint-text">bb</div></div></div>'},

        {'problem_id': '1_6_1', 'choice': ['choice_0'],
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="feedback-hint-multi"><div class="hint-text">aa</div></div></div>'},
        {'problem_id': '1_6_1', 'choice': ['choice_0', 'choice_1'],
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><div class="hint-text">compoundo</div></div>'},

        # The user selects *nothing*, but can still get "unselected" feedback
        {'problem_id': '1_7_1', 'choice': [],
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="feedback-hint-multi"><div class="hint-text">bb</div></div></div>'},
        # 100% not match of sel/unsel feedback
        {'problem_id': '1_7_1', 'choice': ['choice_1'],
         'expected_string': ''},
        # Here we have the correct combination, and that makes feedback too
        {'problem_id': '1_7_1', 'choice': ['choice_0'],
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="feedback-hint-multi"><div class="hint-text">aa</div><div class="hint-text">bb</div></div></div>'},
    )
    @unpack
    def test_checkbox_hints(self, problem_id, choice, expected_string):
        self.maxDiff = None  # pylint: disable=invalid-name
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


class CheckboxHintsTestTracking(HintTest):
    """
    Test the rather complicated tracking log output for checkbox cases.
    """
    xml = """
    <problem>
        <p>question</p>
        <choiceresponse>
        <checkboxgroup>
            <choice correct="true">Apple
              <choicehint selected="true">A true</choicehint>
              <choicehint selected="false">A false</choicehint>
            </choice>
            <choice correct="false">Banana
            </choice>
            <choice correct="true">Cronut
              <choicehint selected="true">C true</choicehint>
            </choice>
            <compoundhint value="A C">A C Compound</compoundhint>
        </checkboxgroup>
        </choiceresponse>
    </problem>
    """
    problem = new_loncapa_problem(xml)

    def test_tracking_log(self):
        """Test checkbox tracking log - by far the most complicated case"""
        # A -> 1 hint
        self.get_hint(u'1_2_1', [u'choice_0'])
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'hint_label': u'<span class="icon fa fa-close" aria-hidden="true"></span>Incorrect',
             'module_id': 'i4x://Foo/bar/mock/abc',
             'problem_part_id': '1_1',
             'choice_all': ['choice_0', 'choice_1', 'choice_2'],
             'correctness': False,
             'trigger_type': 'single',
             'student_answer': [u'choice_0'],
             'hints': [{'text': 'A true', 'trigger': [{'choice': 'choice_0', 'selected': True}]}],
             'question_type': 'choiceresponse'}
        )

        # B C -> 2 hints
        self.problem.capa_module.runtime.track_function.reset_mock()
        self.get_hint(u'1_2_1', [u'choice_1', u'choice_2'])
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'hint_label': u'<span class="icon fa fa-close" aria-hidden="true"></span>Incorrect',
             'module_id': 'i4x://Foo/bar/mock/abc',
             'problem_part_id': '1_1',
             'choice_all': ['choice_0', 'choice_1', 'choice_2'],
             'correctness': False,
             'trigger_type': 'single',
             'student_answer': [u'choice_1', u'choice_2'],
             'hints': [
                 {'text': 'A false', 'trigger': [{'choice': 'choice_0', 'selected': False}]},
                 {'text': 'C true', 'trigger': [{'choice': 'choice_2', 'selected': True}]}
             ],
             'question_type': 'choiceresponse'}
        )

        # A C -> 1 Compound hint
        self.problem.capa_module.runtime.track_function.reset_mock()
        self.get_hint(u'1_2_1', [u'choice_0', u'choice_2'])
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'hint_label': u'<span class="icon fa fa-check" aria-hidden="true"></span>Correct',
             'module_id': 'i4x://Foo/bar/mock/abc',
             'problem_part_id': '1_1',
             'choice_all': ['choice_0', 'choice_1', 'choice_2'],
             'correctness': True,
             'trigger_type': 'compound',
             'student_answer': [u'choice_0', u'choice_2'],
             'hints': [
                 {'text': 'A C Compound',
                  'trigger': [{'choice': 'choice_0', 'selected': True}, {'choice': 'choice_2', 'selected': True}]}
             ],
             'question_type': 'choiceresponse'}
        )


@ddt
class MultpleChoiceHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the multiple choice problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_multiple_choice.xml')
    problem = new_loncapa_problem(xml)

    def test_tracking_log(self):
        """Test that the tracking log comes out right."""
        self.problem.capa_module.reset_mock()
        self.get_hint(u'1_3_1', u'choice_2')
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'module_id': 'i4x://Foo/bar/mock/abc', 'problem_part_id': '1_2', 'trigger_type': 'single',
             'student_answer': [u'choice_2'], 'correctness': False, 'question_type': 'multiplechoiceresponse',
             'hint_label': 'OOPS', 'hints': [{'text': 'Apple is a fruit.'}]}
        )

    @data(
        {'problem_id': u'1_2_1', 'choice': u'choice_0',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><div class="hint-text">Mushroom is a fungus, not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_1',
         'expected_string': ''},
        {'problem_id': u'1_3_1', 'choice': u'choice_1',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">Potato is a root vegetable.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_2',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">OUTSTANDING: </span><div class="hint-text">Apple is indeed a fruit.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': u'choice_2',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label">OOPS: </span><div class="hint-text">Apple is a fruit.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': u'choice_9',
         'expected_string': ''},
    )
    @unpack
    def test_multiplechoice_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


@ddt
class MultpleChoiceHintsWithHtmlTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the multiple choice problem represented by the XML below.

    """
    xml = load_fixture('extended_hints_multiple_choice_with_html.xml')
    problem = new_loncapa_problem(xml)

    def test_tracking_log(self):
        """Test that the tracking log comes out right."""
        self.problem.capa_module.reset_mock()
        self.get_hint(u'1_2_1', u'choice_0')
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'module_id': 'i4x://Foo/bar/mock/abc', 'problem_part_id': '1_1', 'trigger_type': 'single',
             'student_answer': [u'choice_0'], 'correctness': False, 'question_type': 'multiplechoiceresponse',
             'hint_label': '<span class="icon fa fa-close" aria-hidden="true"></span>Incorrect', 'hints': [{'text': 'Mushroom <img src="#" ale="#"/>is a fungus, not a fruit.'}]}
        )

    @data(
        {'problem_id': u'1_2_1', 'choice': u'choice_0',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">Mushroom <img src="#" ale="#"/>is a fungus, not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_1',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">Potato is <img src="#" ale="#"/> not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_2',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text"><a href="#">Apple</a> is a fruit.</div></div>'}
    )
    @unpack
    def test_multiplechoice_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


@ddt
class DropdownHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the drop down problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_dropdown.xml')
    problem = new_loncapa_problem(xml)

    def test_tracking_log(self):
        """Test that the tracking log comes out right."""
        self.problem.capa_module.reset_mock()
        self.get_hint(u'1_3_1', u'FACES')
        self.problem.capa_module.runtime.track_function.assert_called_with(
            'edx.problem.hint.feedback_displayed',
            {'module_id': 'i4x://Foo/bar/mock/abc', 'problem_part_id': '1_2', 'trigger_type': 'single',
             'student_answer': [u'FACES'], 'correctness': True, 'question_type': 'optionresponse',
             'hint_label': '<span class="icon fa fa-check" aria-hidden="true"></span>Correct', 'hints': [{'text': 'With lots of makeup, doncha know?'}]}
        )

    @data(
        {'problem_id': u'1_2_1', 'choice': 'Multiple Choice',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label">Good Job: </span><div class="hint-text">Yes, multiple choice is the right answer.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': 'Text Input',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">No, text input problems do not present options.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': 'Numerical Input',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">No, numerical input problems do not present options.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': 'FACES',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">With lots of makeup, doncha know?</div></div>'},
        {'problem_id': u'1_3_1', 'choice': 'dogs',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label">NOPE: </span><div class="hint-text">Not dogs, not cats, not toads</div></div>'},
        {'problem_id': u'1_3_1', 'choice': 'wrongo',
         'expected_string': ''},

        # Regression case where feedback includes answer substring
        {'problem_id': u'1_4_1', 'choice': 'AAA',
         'expected_string': '<div class="feedback-hint-incorrect"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-close" aria-hidden="true"></span>Incorrect: </span><div class="hint-text">AAABBB1</div></div>'},
        {'problem_id': u'1_4_1', 'choice': 'BBB',
         'expected_string': '<div class="feedback-hint-correct"><div class="explanation-title">Answer:</div><span class="hint-label"><span class="icon fa fa-check" aria-hidden="true"></span>Correct: </span><div class="hint-text">AAABBB2</div></div>'},
        {'problem_id': u'1_4_1', 'choice': 'not going to match',
         'expected_string': ''},
    )
    @unpack
    def test_dropdown_hints(self, problem_id, choice, expected_string):
        hint = self.get_hint(problem_id, choice)
        self.assertEqual(hint, expected_string)


class ErrorConditionsTest(HintTest):
    """
    Erroneous xml should raise exception.
    """
    def test_error_conditions_illegal_element(self):
        xml_with_errors = load_fixture('extended_hints_with_errors.xml')
        with self.assertRaises(Exception):
            new_loncapa_problem(xml_with_errors)    # this problem is improperly constructed
