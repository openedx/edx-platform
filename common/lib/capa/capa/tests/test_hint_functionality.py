# -*- coding: utf-8 -*-
"""
Tests of extended hints
"""


import unittest

from ddt import ddt, data, unpack

from . import new_loncapa_problem, load_fixture


class HintTest(unittest.TestCase):
    """Base class for tests of extended hinting functionality."""

    def _grade_problem(self, problem_id, choice):
        """
        Given a set of student choices for our problem, return the hint message to be shown (if any)
        :param      choice: a single choice made by the student (e.g. 'Multiple Choice')
        :return   the hint message string to be shown
        """
        student_answers = {problem_id: choice}
        resulting_cmap = self.problem.grade_answers(answers=student_answers)    # pylint: disable=no-member
        adict = resulting_cmap.cmap.get(problem_id)
        if adict:
            return adict['msg']
        else:
            return ''

    def _check_student_selection_result(self, problem_id, choice, expected_string, expect_failure=False):
        """
        This helper function simplifies a call to either 'assertNotEqual' or 'assertEqual' to
        make the tests in this file easier to read.
        """
        message_text = self._grade_problem(problem_id, choice)
        if expect_failure:
            self.assertNotEqual(
                message_text,
                expected_string,
                '\n   The produced HTML hint string:\n                           ' + message_text +
                '\n   Should not have matched the expected HTML:\n                           ' + expected_string)
        else:
            self.assertEqual(
                message_text,
                expected_string,
                '\nThe produced HTML hint string:\n                           ' + message_text +
                '\nDoes not match the expected HTML:\n                           ' + expected_string)


@ddt
class TextInputHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the text input problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)          # this problem is properly constructed

    def test_text_input_hints_regex(self):
        """
        Test that regular expression hints are properly triggered.
        """
        # a correctly constructed regex hint
        self._check_student_selection_result(
            u'1_2_1', 'Disneyland',
            u'<div class="feedback_hint_incorrect">Incorrect: The country name does not end in LAND</div>'
        )

    @data(
        {'problem_id': u'1_2_1', 'choice': 'Germany', 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: I do not think so.</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'Germany', 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: I do not think so.</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'france', 'expected_string': u'<div class="feedback_hint_correct">Correct: Viva la France!</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'France', 'expected_string': u'<div class="feedback_hint_correct">Correct: Viva la France!</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'Mexico', 'expected_string': '', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'USA', 'expected_string': u'<div class="feedback_hint_correct">Correct: Less well known, but yes, there is a Paris, Texas.</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'usa', 'expected_string': u'<div class="feedback_hint_correct">Correct: Less well known, but yes, there is a Paris, Texas.</div>', 'expect_failure': False},
        {'problem_id': u'1_2_1', 'choice': 'uSAx', 'expected_string': u'<div class="feedback_hint_correct">Correct: Less well known, but yes, there is a Paris, Texas.</div>', 'expect_failure': True},
        {'problem_id': u'1_3_1', 'choice': 'Blue', 'expected_string': u'<div class="feedback_hint_correct">Correct: The red light is scattered by water molecules leaving only blue light.</div>', 'expect_failure': False},
        {'problem_id': u'1_3_1', 'choice': 'bluex', 'expected_string': u'<div class="feedback_hint_correct">Correct: The red light is scattered by water molecules leaving only blue light.</div>', 'expect_failure': True},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, expected_string, expect_failure):
        self._check_student_selection_result(problem_id, choice, expected_string, expect_failure)


@ddt
class TextInputHintsManyCombinations(HintTest):
    """
    Test text input combinations with additional answers.
    """
    xml = load_fixture('extended_hints_text_input.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_5_1', 'choice': 'A', 'expected_string': '<div class="feedback_hint_correct">Woo Hoo: hint1</div>'},
        {'problem_id': u'1_5_1', 'choice': 'a', 'expected_string': ''},
        {'problem_id': u'1_5_1', 'choice': 'B', 'expected_string': '<div class="feedback_hint_correct">Correct: hint2</div>'},
        {'problem_id': u'1_5_1', 'choice': 'b', 'expected_string': '<div class="feedback_hint_correct">Correct: hint2</div>'},
        {'problem_id': u'1_5_1', 'choice': 'C', 'expected_string': '<div class="feedback_hint_correct">Correct: hint3</div>'},
        {'problem_id': u'1_5_1', 'choice': 'c', 'expected_string': ''},
        {'problem_id': u'1_5_1', 'choice': 'D', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint4</div>'},
        {'problem_id': u'1_5_1', 'choice': 'd', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint4</div>'},
        {'problem_id': u'1_5_1', 'choice': 'E', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint5</div>'},
        {'problem_id': u'1_5_1', 'choice': 'e', 'expected_string': ''},

        {'problem_id': u'1_5_1', 'choice': 'FGG', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint6</div>'},
        {'problem_id': u'1_5_1', 'choice': 'fgG', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint6</div>'},

        {'problem_id': u'1_5_1', 'choice': 'HIII', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: hint7</div>'},
        {'problem_id': u'1_5_1', 'choice': 'hiIi', 'expected_string': ''},

        {'problem_id': u'1_5_1', 'choice': 'abc', 'expected_string': ''},

        # verify the implicit ^ .. $ of regex matching, so none of these match
        {'problem_id': u'1_5_1', 'choice': 'xHIII', 'expected_string': ''},
        {'problem_id': u'1_5_1', 'choice': 'HIIIx', 'expected_string': ''},
        {'problem_id': u'1_5_1', 'choice': 'xHIIIx', 'expected_string': ''},
    )
    @unpack
    def test_text_input_hints(self, problem_id, choice, expected_string):
        message_text = self._grade_problem(problem_id, choice)
        self.assertEqual(message_text, expected_string)


@ddt
class NumericInputHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the numeric input problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_numeric_input.xml')
    problem = new_loncapa_problem(xml)          # this problem is properly constructed

    @data(
        {'problem_id': u'1_2_1', 'choice': '1.141', 'expected_string': u'<div class="feedback_hint_correct">Nice: The square root of two turns up in the strangest places.</div>'},
        {'problem_id': u'1_3_1', 'choice': '4', 'expected_string': u'<div class="feedback_hint_correct">Correct: Pretty easy, uh?.</div>'},
        # should get hint, when correct via numeric-tolerance
        {'problem_id': u'1_2_1', 'choice': '1.15', 'expected_string': u'<div class="feedback_hint_correct">Nice: The square root of two turns up in the strangest places.</div>'},
        # when they answer wrong, nothing
        {'problem_id': u'1_2_1', 'choice': '2', 'expected_string': ''},

    )
    @unpack
    def test_numeric_input_hints(self, problem_id, choice, expected_string):
        self._check_student_selection_result(problem_id, choice, expected_string, False)


@ddt
class CheckboxHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the checkbox problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_checkbox.xml')
    problem = new_loncapa_problem(xml)          # this problem is properly constructed

    @data(
        {'problem_id': u'1_2_1', 'choice': [u'choice_0'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">You are right that apple is a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not fruit</div><div class="feedback_hint_text">Remember that grape is also a fruit.</div><div class="feedback_hint_text">What is a camero anyway?</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_1'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">Remember that apple is also a fruit.</div><div class="feedback_hint_text">Mushroom is a fungus, not a fruit.</div><div class="feedback_hint_text">Remember that grape is also a fruit.</div><div class="feedback_hint_text">What is a camero anyway?</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_2'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">Remember that apple is also a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not fruit</div><div class="feedback_hint_text">You are right that grape is a fruit</div><div class="feedback_hint_text">What is a camero anyway?</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_3'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">Remember that apple is also a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not fruit</div><div class="feedback_hint_text">Remember that grape is also a fruit.</div><div class="feedback_hint_text">What is a camero anyway?</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_4'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">Remember that apple is also a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not fruit</div><div class="feedback_hint_text">Remember that grape is also a fruit.</div><div class="feedback_hint_text">I do not know what a Camero is but it is not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_0', u'choice_1'], 'expected_string': u'<div class="feedback_hint_incorrect">Almost right: <div class="feedback_hint_text">You are right that apple is a fruit, but there is one you are missing. Also, mushroom is not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_1', u'choice_2'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">You are right that grape is a fruit, but there is one you are missing. Also, mushroom is not a fruit.</div></div>'},
        {'problem_id': u'1_2_1', 'choice': [u'choice_0', u'choice_2'], 'expected_string': u'<div class="feedback_hint_correct">Correct: <div class="feedback_hint_text">You are right that apple is a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not fruit</div><div class="feedback_hint_text">You are right that grape is a fruit</div><div class="feedback_hint_text">What is a camero anyway?</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">No, sorry, a banana is a fruit.</div><div class="feedback_hint_text">You are right that mushrooms are not vegatbles</div><div class="feedback_hint_text">Brussel sprout is the only vegetable in this list.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_1'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">poor banana.</div><div class="feedback_hint_text">You are right that mushrooms are not vegatbles</div><div class="feedback_hint_text">Brussel sprout is the only vegetable in this list.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_2'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">poor banana.</div><div class="feedback_hint_text">Mushroom is a fungus, not a vegetable.</div><div class="feedback_hint_text">Brussel sprout is the only vegetable in this list.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_3'], 'expected_string': u'<div class="feedback_hint_correct">Correct: <div class="feedback_hint_text">poor banana.</div><div class="feedback_hint_text">You are right that mushrooms are not vegatbles</div><div class="feedback_hint_text">Brussel sprouts are vegetables.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0', u'choice_1'], 'expected_string': u'<div class="feedback_hint_incorrect">Very funny: <div class="feedback_hint_text">Making a banana split?</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_1', u'choice_2'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">poor banana.</div><div class="feedback_hint_text">Mushroom is a fungus, not a vegetable.</div><div class="feedback_hint_text">Brussel sprout is the only vegetable in this list.</div></div>'},
        {'problem_id': u'1_3_1', 'choice': [u'choice_0', u'choice_2'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">No, sorry, a banana is a fruit.</div><div class="feedback_hint_text">Mushroom is a fungus, not a vegetable.</div><div class="feedback_hint_text">Brussel sprout is the only vegetable in this list.</div></div>'},

        # check for interaction between compoundhint and correct/incorrect
        {'problem_id': u'1_4_1', 'choice': [u'choice_0', u'choice_1'], 'expected_string': u'<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">AB</div></div>'},
        {'problem_id': u'1_4_1', 'choice': [u'choice_0', u'choice_2'], 'expected_string': u'<div class="feedback_hint_correct">Correct: <div class="feedback_hint_text">AC</div></div>'},

        # check for labeling where multiple child hints have labels
        # These are some tricky cases
        {'problem_id': '1_5_1', 'choice': ['choice_0', 'choice_1'], 'expected_string': '<div class="feedback_hint_correct">AA: <div class="feedback_hint_text">aa</div></div>'},
        {'problem_id': '1_5_1', 'choice': ['choice_0'], 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: <div class="feedback_hint_text">aa</div><div class="feedback_hint_text">bb</div></div>'},
        {'problem_id': '1_5_1', 'choice': ['choice_1'], 'expected_string': ''},
        {'problem_id': '1_5_1', 'choice': [], 'expected_string': '<div class="feedback_hint_incorrect">BB: <div class="feedback_hint_text">bb</div></div>'},

    )
    @unpack
    def test_checkbox_hints(self, problem_id, choice, expected_string):
        self._check_student_selection_result(problem_id, choice, expected_string, False)


@ddt
class MultpleChoiceHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the multiple choice problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_multiple_choice.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_2_1', 'choice': u'choice_0', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: Mushroom is a fungus, not a fruit.</div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_1', 'expected_string': ''},
        {'problem_id': u'1_3_1', 'choice': u'choice_1', 'expected_string': '<div class="feedback_hint_correct">Correct: Potato is a root vegetable.</div>'},
        {'problem_id': u'1_2_1', 'choice': u'choice_2', 'expected_string': '<div class="feedback_hint_correct">OUTSTANDING: Apple is indeed a fruit.</div>'},
        {'problem_id': u'1_3_1', 'choice': u'choice_2', 'expected_string': '<div class="feedback_hint_incorrect">OOPS: Apple is a fruit.</div>'},
        {'problem_id': u'1_3_1', 'choice': u'choice_9', 'expected_string': ''},
    )
    @unpack
    def test_multiplechoice_hints(self, problem_id, choice, expected_string):
        self._check_student_selection_result(problem_id, choice, expected_string, False)


@ddt
class DropdownHintsTest(HintTest):
    """
    This class consists of a suite of test cases to be run on the drop down problem represented by the XML below.
    """
    xml = load_fixture('extended_hints_dropdown.xml')
    problem = new_loncapa_problem(xml)

    @data(
        {'problem_id': u'1_2_1', 'choice': 'Multiple Choice', 'expected_string': '<div class="feedback_hint_correct">Good Job: Yes, multiple choice is the right answer.</div>'},
        {'problem_id': u'1_2_1', 'choice': 'Text Input', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: No, text input problems do not present options.</div>'},
        {'problem_id': u'1_2_1', 'choice': 'Numerical Input', 'expected_string': '<div class="feedback_hint_incorrect">Incorrect: No, numerical input problems do not present options.</div>'},
        {'problem_id': u'1_3_1', 'choice': 'FACES', 'expected_string': '<div class="feedback_hint_correct">Correct: With lots of makeup, doncha know?</div>'},
        {'problem_id': u'1_3_1', 'choice': 'dogs', 'expected_string': '<div class="feedback_hint_incorrect">NOPE: Not dogs, not cats, not toads</div>'},
        {'problem_id': u'1_3_1', 'choice': 'wrongo', 'expected_string': ''},
    )
    @unpack
    def test_dropdown_hints(self, problem_id, choice, expected_string):
        self._check_student_selection_result(problem_id, choice, expected_string, False)


class ErrorConditionsTest(HintTest):
    """
    Intentional errors are exercised.
    """

    def test_error_conditions_illegal_element(self):
        xml_with_errors = load_fixture('extended_hints_with_errors.xml')
        with self.assertRaises(Exception):
            new_loncapa_problem(xml_with_errors)    # this problem is improperly constructed
