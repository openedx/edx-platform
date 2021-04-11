"""
Bok choy acceptance and a11y tests for problem types in the LMS
"""


import random
import textwrap
from abc import ABCMeta, abstractmethod

import ddt
import six
from bok_choy.promise import BrokenPromise

from capa.tests.response_xml_factory import (
    AnnotationResponseXMLFactory,
    ChoiceResponseXMLFactory,
    ChoiceTextResponseXMLFactory,
    CodeResponseXMLFactory,
    CustomResponseXMLFactory,
    FormulaResponseXMLFactory,
    JSInputXMLFactory,
    MultipleChoiceResponseXMLFactory,
    NumericalResponseXMLFactory,
    OptionResponseXMLFactory,
    StringResponseXMLFactory,
    SymbolicResponseXMLFactory
)
from common.test.acceptance.fixtures.course import XBlockFixtureDesc
from common.test.acceptance.pages.lms.problem import ProblemPage
from common.test.acceptance.tests.helpers import EventsTestMixin, select_option_by_text
from common.test.acceptance.tests.lms.test_lms_problems import ProblemsTest
from openedx.core.lib.tests import attr


class ProblemTypeTestBaseMeta(ABCMeta):
    """
    MetaClass for ProblemTypeTestBase to ensure that the required attributes
    are defined in the inheriting classes.
    """
    def __call__(cls, *args, **kwargs):
        obj = type.__call__(cls, *args, **kwargs)

        required_attrs = [
            'problem_name',
            'problem_type',
            'factory',
            'factory_kwargs',
            'status_indicators',
        ]

        for required_attr in required_attrs:
            msg = (u'{} is a required attribute for {}').format(
                required_attr, str(cls)
            )

            try:
                if obj.__getattribute__(required_attr) is None:
                    raise NotImplementedError(msg)
            except AttributeError:
                raise NotImplementedError(msg)

        return obj


class ProblemTypeTestBase(six.with_metaclass(ProblemTypeTestBaseMeta, ProblemsTest, EventsTestMixin)):
    """
    Base class for testing assesment problem types in bok choy.

    This inherits from ProblemsTest, which has capabilities for testing problem
    features that are not problem type specific (checking, hinting, etc.).

    The following attributes must be explicitly defined when inheriting from
    this class:
        problem_name (str)
        problem_type (str)
        factory (ResponseXMLFactory subclass instance)

    Additionally, the default values for factory_kwargs and status_indicators
    may need to be overridden for some problem types.
    """

    problem_name = None
    problem_type = None
    problem_points = 1
    factory = None
    factory_kwargs = {}
    status_indicators = {
        'correct': ['span.correct'],
        'incorrect': ['span.incorrect'],
        'unanswered': ['span.unanswered'],
        'submitted': ['span.submitted'],
        'unsubmitted': ['.unsubmitted']
    }

    def setUp(self):
        """
        Visits courseware_page and defines self.problem_page.
        """
        super(ProblemTypeTestBase, self).setUp()
        self.courseware_page.visit()
        self.problem_page = ProblemPage(self.browser)

    def get_sequential(self):
        """ Allow any class in the inheritance chain to customize subsection metadata."""
        return XBlockFixtureDesc('sequential', 'Test Subsection', metadata=getattr(self, 'sequential_metadata', {}))

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'always', 'show_reset_button': True}
        )

    def wait_for_status(self, status):
        """
        Waits for the expected status indicator.

        Args:
            status: one of ("correct", "incorrect", "unanswered", "submitted")
        """
        msg = u"Wait for status to be {}".format(status)
        selector = ', '.join(self.status_indicators[status])
        self.problem_page.wait_for_element_visibility(selector, msg)

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    @abstractmethod
    def answer_problem(self, correctness):
        """
        Args:
            `correct` (bool): Inputs correct answer if True, else inputs
                incorrect answer.
        """
        raise NotImplementedError()


class ProblemTypeA11yTestMixin(object):
    """
    Shared a11y tests for all problem types.
    """
    @attr('a11y')
    def test_problem_type_a11y(self):
        """
        Run accessibility audit for the problem type.
        """
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        # Set the scope to the problem container
        self.problem_page.a11y_audit.config.set_scope(
            include=['div#seq_content']
        )

        # Run the accessibility audit.
        self.problem_page.a11y_audit.check_for_accessibility_errors()


class AnnotationProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Annotation Problem Type
    """
    problem_name = 'ANNOTATION TEST PROBLEM'
    problem_type = 'annotationresponse'
    problem_points = 2

    factory = AnnotationResponseXMLFactory()
    partially_correct = True

    can_submit_blank = True
    can_update_save_notification = False
    factory_kwargs = {
        'title': 'Annotation Problem',
        'text': 'The text being annotated',
        'comment': 'What do you think the about this text?',
        'comment_prompt': 'Type your answer below.',
        'tag_prompt': 'Which of these items most applies to the text?',
        'options': [
            ('dog', 'correct'),
            ('cat', 'incorrect'),
            ('fish', 'partially-correct'),
        ]
    }

    status_indicators = {
        'correct': ['span.correct'],
        'incorrect': ['span.incorrect'],
        'partially-correct': ['span.partially-correct'],
        'unanswered': ['span.unanswered'],
        'submitted': ['span.submitted'],
    }

    def setUp(self, *args, **kwargs):
        """
        Additional setup for AnnotationProblemTypeBase
        """
        super(AnnotationProblemTypeBase, self).setUp(*args, **kwargs)

        self.problem_page.a11y_audit.config.set_rules({
            "ignore": [
                'label',  # TODO: AC-491
                'label-title-only',  # TODO: AC-493
            ]
        })

    def answer_problem(self, correctness):
        """
        Answer annotation problem.
        """
        if correctness == 'correct':
            choice = 0
        elif correctness == 'partially-correct':
            choice = 2
        else:
            choice = 1
        answer = 'Student comment'

        self.problem_page.q(css='div.problem textarea.comment').fill(answer)
        self.problem_page.q(
            css='div.problem span.tag'.format(choice=choice)
        ).nth(choice).click()


class AnnotationProblemTypeTest(AnnotationProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Annotation Problem Type
    """
    shard = 20
    pass


class CheckboxProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization Checkbox Problem Type
    """
    problem_name = 'CHECKBOX TEST PROBLEM'
    problem_type = 'checkbox'
    partially_correct = True

    factory = ChoiceResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The correct answer is Choice 0 and Choice 2, Choice 1 and Choice 3 together are incorrect.',
        'choice_type': 'checkbox',
        'credit_type': 'edc',
        'choices': [True, False, True, False],
        'choice_names': ['Choice 0', 'Choice 1', 'Choice 2', 'Choice 3'],
        'explanation_text': 'This is explanation text'
    }

    def answer_problem(self, correctness):
        """
        Answer checkbox problem.
        """
        if correctness == 'correct':
            self.problem_page.click_choice("choice_0")
            self.problem_page.click_choice("choice_2")
        elif correctness == 'partially-correct':
            self.problem_page.click_choice("choice_2")
        else:
            self.problem_page.click_choice("choice_1")
            self.problem_page.click_choice("choice_3")


@ddt.ddt
class CheckboxProblemTypeTest(CheckboxProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Checkbox Problem Type
    """
    shard = 18


class CheckboxProblemTypeTestNonRandomized(CheckboxProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for the non-randomized checkbox problem
    """

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


@ddt.ddt
class MultipleChoiceProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization Multiple Choice Problem Type
    """
    problem_name = 'MULTIPLE CHOICE TEST PROBLEM'
    problem_type = 'multiple choice'

    factory = MultipleChoiceResponseXMLFactory()

    partially_correct = False

    factory_kwargs = {
        'question_text': 'The correct answer is Choice 2',
        'choices': [False, False, True, False],
        'choice_names': ['choice_0', 'choice_1', 'choice_2', 'choice_3'],
    }
    status_indicators = {
        'correct': ['label.choicegroup_correct'],
        'incorrect': ['label.choicegroup_incorrect', 'span.incorrect'],
        'unanswered': ['span.unanswered'],
        'submitted': ['label.choicegroup_submitted', 'span.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer multiple choice problem.
        """
        if correctness == 'incorrect':
            self.problem_page.click_choice("choice_choice_1")
        else:
            self.problem_page.click_choice("choice_choice_2")


@ddt.ddt
class MultipleChoiceProblemTypeTest(MultipleChoiceProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Multiple Choice Problem Type
    """
    shard = 24


@ddt.ddt
class MultipleChoiceProblemTypeTestNonRandomized(MultipleChoiceProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized multiple choice problem
    """
    shard = 24

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True, 'max_attempts': 3}
        )


class RadioProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Radio Problem Type
    """
    problem_name = 'RADIO TEST PROBLEM'
    problem_type = 'radio'

    partially_correct = False

    factory = ChoiceResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The correct answer is Choice 2',
        'choice_type': 'radio',
        'choices': [False, False, True, False],
        'choice_names': ['Choice 0', 'Choice 1', 'Choice 2', 'Choice 3'],
    }
    status_indicators = {
        'correct': ['label.choicegroup_correct'],
        'incorrect': ['label.choicegroup_incorrect', 'span.incorrect'],
        'unanswered': ['span.unanswered'],
        'submitted': ['label.choicegroup_submitted', 'span.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer radio problem.
        """
        if correctness == 'correct':
            self.problem_page.click_choice("choice_2")
        else:
            self.problem_page.click_choice("choice_1")


@ddt.ddt
class RadioProblemTypeTest(RadioProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Multiple Radio Problem Type
    """
    shard = 24
    pass


class RadioProblemTypeTestNonRandomized(RadioProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized radio problem
    """
    shard = 8

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


class DropDownProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Drop Down Problem Type
    """
    problem_name = 'DROP DOWN TEST PROBLEM'
    problem_type = 'drop down'

    partially_correct = False

    factory = OptionResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The correct answer is Option 2',
        'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
        'correct_option': 'Option 2'
    }

    def answer_problem(self, correctness):
        """
        Answer drop down problem.
        """
        answer = 'Option 2' if correctness == 'correct' else 'Option 3'
        selector_element = self.problem_page.q(
            css='.problem .option-input select')
        select_option_by_text(selector_element, answer)


@ddt.ddt
class DropdownProblemTypeTest(DropDownProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Dropdown Problem Type
    """
    shard = 8
    pass


@ddt.ddt
class DropDownProblemTypeTestNonRandomized(DropDownProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized Dropdown problem
    """
    shard = 8

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


class StringProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for String Problem Type
    """
    problem_name = 'STRING TEST PROBLEM'
    problem_type = 'string'

    partially_correct = False

    factory = StringResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The answer is "correct string"',
        'case_sensitive': False,
        'answer': 'correct string',
    }

    status_indicators = {
        'correct': ['div.correct'],
        'incorrect': ['div.incorrect'],
        'unanswered': ['div.unanswered', 'div.unsubmitted'],
        'submitted': ['span.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer string problem.
        """
        textvalue = 'correct string' if correctness == 'correct' else 'incorrect string'
        self.problem_page.fill_answer(textvalue)


class StringProblemTypeTest(StringProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the String Problem Type
    """
    shard = 8
    pass


class NumericalProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Numerical Problem Type
    """
    problem_name = 'NUMERICAL TEST PROBLEM'
    problem_type = 'numerical'
    partially_correct = False

    factory = NumericalResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The answer is pi + 1',
        'answer': '4.14159',
        'tolerance': '0.00001',
        'math_display': True,
    }

    status_indicators = {
        'correct': ['div.correct'],
        'incorrect': ['div.incorrect'],
        'unanswered': ['div.unanswered', 'div.unsubmitted'],
        'submitted': ['div.submitted'],
        'unsubmitted': ['div.unsubmitted']
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer numerical problem.
        """
        textvalue = ''
        if correctness == 'correct':
            textvalue = "pi + 1"
        elif correctness == 'error':
            textvalue = 'notNum'
        else:
            textvalue = str(random.randint(-2, 2))
        self.problem_page.fill_answer(textvalue)


@ddt.ddt
class NumericalProblemTypeTest(NumericalProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Numerical Problem Type
    """
    shard = 12


@ddt.ddt
class NumericalProblemTypeTestNonRandomized(NumericalProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized Numerical problem
    """
    shard = 12

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


@ddt.ddt
class FormulaProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Formula Problem Type
    """
    problem_name = 'FORMULA TEST PROBLEM'
    problem_type = 'formula'
    partially_correct = False

    factory = FormulaResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The solution is [mathjax]x^2+2x+y[/mathjax]',
        'sample_dict': {'x': (-100, 100), 'y': (-100, 100)},
        'num_samples': 10,
        'tolerance': 0.00001,
        'math_display': True,
        'answer': 'x^2+2*x+y',
    }

    status_indicators = {
        'correct': ['div.correct'],
        'incorrect': ['div.incorrect'],
        'unanswered': ['div.unanswered', 'div.unsubmitted'],
        'submitted': ['div.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer formula problem.
        """
        textvalue = "x^2+2*x+y" if correctness == 'correct' else 'x^2'
        self.problem_page.fill_answer(textvalue)


@ddt.ddt
class ScriptProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Script Problem Type
    """
    problem_name = 'SCRIPT TEST PROBLEM'
    problem_type = 'script'
    problem_points = 2
    partially_correct = False

    factory = CustomResponseXMLFactory()

    factory_kwargs = {
        'cfn': 'test_add_to_ten',
        'expect': '10',
        'num_inputs': 2,
        'question_text': 'Enter two integers that sum to 10.',
        'input_element_label': 'Enter an integer',
        'script': textwrap.dedent("""
            def test_add_to_ten(expect,ans):
                try:
                    a1=int(ans[0])
                    a2=int(ans[1])
                except ValueError:
                    a1=0
                    a2=0
                return (a1+a2)==int(expect)
        """),
    }
    status_indicators = {
        'correct': ['div.correct'],
        'incorrect': ['div.incorrect'],
        'unanswered': ['div.unanswered', 'div.unsubmitted'],
        'submitted': ['div.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status is present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def answer_problem(self, correctness):
        """
        Answer script problem.
        """
        # Correct answer is any two integers that sum to 10
        first_addend = random.randint(-100, 100)
        second_addend = 10 - first_addend

        # If we want an incorrect answer, then change
        # the second addend so they no longer sum to 10
        if not correctness == 'correct':
            second_addend += random.randint(1, 10)

        self.problem_page.fill_answer(first_addend, input_num=0)
        self.problem_page.fill_answer(second_addend, input_num=1)


@ddt.ddt
class ScriptProblemTypeTest(ScriptProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Script Problem Type
    """
    shard = 20
    pass


class ScriptProblemTypeTestNonRandomized(ScriptProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized Script problem
    """
    shard = 8

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


class JSInputTypeTest(ProblemTypeTestBase, ProblemTypeA11yTestMixin):
    """
    TestCase Class for jsinput (custom JavaScript) problem type.
    Right now the only test point that is executed is the a11y test.
    This is because the factory simply creates an empty iframe.
    """
    problem_name = 'JSINPUT PROBLEM'
    problem_type = 'customresponse'

    factory = JSInputXMLFactory()

    factory_kwargs = {
        'question_text': 'IFrame shows below (but has no content)'
    }

    def answer_problem(self, correctness):
        """
        Problem is not set up to work (displays an empty iframe), but this method must
        be extended because the parent class has marked it as abstract.
        """
        raise NotImplementedError()


class CodeProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Code Problem Type
    """
    problem_name = 'CODE TEST PROBLEM'
    problem_type = 'code'
    partially_correct = False
    can_update_save_notification = False
    factory = CodeResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'Submit code to an external grader',
        'initial_display': 'print "Hello world!"',
        'grader_payload': '{"grader": "ps1/Spring2013/test_grader.py"}',
    }

    status_indicators = {
        'correct': ['.grader-status .correct ~ .debug'],
        'incorrect': ['.grader-status .incorrect ~ .debug'],
        'unanswered': ['.grader-status .unanswered ~ .debug'],
        'submitted': ['.grader-status .submitted ~ .debug'],
    }

    def answer_problem(self, correctness):
        """
        Answer code problem.
        """
        # The fake xqueue server is configured to respond
        # correct / incorrect no matter what we submit.
        # Furthermore, since the inline code response uses
        # JavaScript to make the code display nicely, it's difficult
        # to programatically input text
        # (there's not <textarea> we can just fill text into)
        # For this reason, we submit the initial code in the response
        # (configured in the problem XML above)
        pass


class CodeProblemTypeTest(CodeProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Code Problem Type
    """
    shard = 12

    def wait_for_status(self, status):
        """
        Overridden for script test because the testing grader always responds
        with "correct"
        """
        pass


class ChoiceTextProblemTypeTestBase(ProblemTypeTestBase):
    """
    Base class for "Choice + Text" Problem Types.
    (e.g. RadioText, CheckboxText)
    """
    choice_type = None
    partially_correct = False
    can_update_save_notification = False

    def _select_choice(self, input_num):
        """
        Selects the nth (where n == input_num) choice of the problem.
        """
        self.problem_page.q(
            css=u'div.problem input.ctinput[type="{}"]'.format(self.choice_type)
        ).nth(input_num).click()

    def _fill_input_text(self, value, input_num):
        """
        Fills the nth (where n == input_num) text input field of the problem
        with value.
        """
        self.problem_page.q(
            css='div.problem input.ctinput[type="text"]'
        ).nth(input_num).fill(value)

    def answer_problem(self, correctness):
        """
        Answer radio text problem.
        """
        choice = 0 if correctness == 'correct' else 1
        input_value = "8" if correctness == 'correct' else "5"

        self._select_choice(choice)
        self._fill_input_text(input_value, choice)


class RadioTextProblemTypeBase(ChoiceTextProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Radio Text Problem Type
    """
    problem_name = 'RADIO TEXT TEST PROBLEM'
    problem_type = 'radio_text'
    choice_type = 'radio'
    partially_correct = False
    can_update_save_notification = False

    factory = ChoiceTextResponseXMLFactory()

    factory_kwargs = {
        'question_text': 'The correct answer is Choice 0 and input 8',
        'type': 'radiotextgroup',
        'choices': [
            ("true", {"answer": "8", "tolerance": "1"}),
            ("false", {"answer": "8", "tolerance": "1"}),
        ],
    }

    status_indicators = {
        'correct': ['section.choicetextgroup_correct'],
        'incorrect': ['section.choicetextgroup_incorrect', 'span.incorrect'],
        'unanswered': ['span.unanswered'],
        'submitted': ['section.choicetextgroup_submitted', 'span.submitted'],
    }

    def problem_status(self, status):
        """
        Returns the status of problem
        Args:
            status(string): status of the problem which is to be checked

        Returns:
            True: If provided status is present on the page
            False: If provided status is not present on the page
        """
        selector = ', '.join(self.status_indicators[status])
        try:
            self.problem_page.wait_for_element_visibility(selector, 'Status not present', timeout=10)
            return True
        except BrokenPromise:
            return False

    def setUp(self, *args, **kwargs):
        """
        Additional setup for RadioTextProblemTypeBase
        """
        super(RadioTextProblemTypeBase, self).setUp(*args, **kwargs)

        self.problem_page.a11y_audit.config.set_rules({
            "ignore": [
                'radiogroup',  # TODO: AC-491
                'label',  # TODO: AC-491
                'section',  # TODO: AC-491
            ]
        })


@ddt.ddt
class RadioTextProblemTypeTest(RadioTextProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Radio Text Problem Type
    """
    shard = 8
    pass


class RadioTextProblemTypeTestNonRandomized(RadioTextProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized Radio text problem
    """
    shard = 24

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


class CheckboxTextProblemTypeBase(ChoiceTextProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization for Checkbox Text Problem Type
    """
    problem_name = 'CHECKBOX TEXT TEST PROBLEM'
    problem_type = 'checkbox_text'
    choice_type = 'checkbox'
    factory = ChoiceTextResponseXMLFactory()
    partially_correct = False
    can_update_save_notification = False

    factory_kwargs = {
        'question_text': 'The correct answer is Choice 0 and input 8',
        'type': 'checkboxtextgroup',
        'choices': [
            ("true", {"answer": "8", "tolerance": "1"}),
            ("false", {"answer": "8", "tolerance": "1"}),
        ],
    }

    def setUp(self, *args, **kwargs):
        """
        Additional setup for CheckboxTextProblemTypeBase
        """
        super(CheckboxTextProblemTypeBase, self).setUp(*args, **kwargs)

        self.problem_page.a11y_audit.config.set_rules({
            "ignore": [
                'checkboxgroup',  # TODO: AC-491
                'label',  # TODO: AC-491
                'section',  # TODO: AC-491
            ]
        })


class CheckboxTextProblemTypeTest(CheckboxTextProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Checkbox Text Problem Type
    """
    pass


class CheckboxTextProblemTypeTestNonRandomized(CheckboxTextProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Tests for non-randomized Checkbox problem
    """

    def get_problem(self):
        """
        Creates a {problem_type} problem
        """
        # Generate the problem XML using capa.tests.response_xml_factory
        return XBlockFixtureDesc(
            'problem',
            self.problem_name,
            data=self.factory.build_xml(**self.factory_kwargs),
            metadata={'rerandomize': 'never', 'show_reset_button': True}
        )


class SymbolicProblemTypeBase(ProblemTypeTestBase):
    """
    ProblemTypeTestBase specialization  for Symbolic Problem Type
    """
    problem_name = 'SYMBOLIC TEST PROBLEM'
    problem_type = 'symbolicresponse'
    partially_correct = False

    factory = SymbolicResponseXMLFactory()

    factory_kwargs = {
        'expect': '2*x+3*y',
        'question_text': 'Enter a value'
    }

    status_indicators = {
        'correct': ['div.capa_inputtype div.correct'],
        'incorrect': ['div.capa_inputtype div.incorrect'],
        'unanswered': ['div.capa_inputtype div.unanswered'],
        'submitted': ['div.capa_inputtype div.submitted'],
    }

    def answer_problem(self, correctness):
        """
        Answer symbolic problem.
        """
        choice = "2*x+3*y" if correctness == 'correct' else "3*a+4*b"
        self.problem_page.fill_answer(choice)


class SymbolicProblemTypeTest(SymbolicProblemTypeBase, ProblemTypeA11yTestMixin):
    """
    Standard tests for the Symbolic Problem Type
    """
    pass
