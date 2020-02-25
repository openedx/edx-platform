"""
Bok choy acceptance and a11y tests for problem types in the LMS
"""


import random
import textwrap
from abc import ABCMeta, abstractmethod

import ddt
import pytest
import six
from bok_choy.promise import BrokenPromise
from six.moves import range

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


@ddt.ddt
class ProblemTypeTestMixin(ProblemTypeA11yTestMixin):
    """
    Test cases shared amongst problem types.
    """
    can_submit_blank = False
    can_update_save_notification = True

    @attr(shard=11)
    def test_answer_correctly(self):
        """
        Scenario: I can answer a problem correctly
        Given External graders respond "correct"
        And I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "correctly"
        Then my "<ProblemType>" answer is marked "correct"
        And The "<ProblemType>" problem displays a "correct" answer
        And a success notification is shown
        And clicking on "Review" moves focus to the problem meta area
        And a "problem_check" server event is emitted
        And a "problem_check" browser event is emitted
        """
        # Make sure we're looking at the right problem
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        # Answer the problem correctly
        self.answer_problem(correctness='correct')
        self.problem_page.click_submit()
        self.wait_for_status('correct')
        self.problem_page.wait_success_notification()
        # Check that clicking on "Review" goes to the problem meta location
        self.problem_page.click_review_in_notification(notification_type='submit')
        self.problem_page.wait_for_focus_on_problem_meta()

        # Check for corresponding tracking event
        expected_events = [
            {
                'event_source': 'server',
                'event_type': 'problem_check',
                'username': self.username,
            }, {
                'event_source': 'browser',
                'event_type': 'problem_check',
                'username': self.username,
            },
        ]

        for event in expected_events:
            self.wait_for_events(event_filter=event, number_of_matches=1)

    @attr(shard=11)
    def test_answer_incorrectly(self):
        """
        Scenario: I can answer a problem incorrectly
        Given External graders respond "incorrect"
        And I am viewing a "<ProblemType>" problem
        When I answer a "<ProblemType>" problem "incorrectly"
        Then my "<ProblemType>" answer is marked "incorrect"
        And The "<ProblemType>" problem displays a "incorrect" answer
        """
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        # Answer the problem incorrectly
        self.answer_problem(correctness='incorrect')
        self.problem_page.click_submit()
        self.wait_for_status('incorrect')
        self.problem_page.wait_incorrect_notification()

    @attr(shard=11)
    def test_submit_blank_answer(self):
        """
        Scenario: I can submit a blank answer
        Given I am viewing a "<ProblemType>" problem
        When I submit a problem
        Then my "<ProblemType>" answer is marked "incorrect"
        And The "<ProblemType>" problem displays a "blank" answer
        """
        if not self.can_submit_blank:
            pytest.skip("Test incompatible with the current problem type")

        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )
        # Leave the problem unchanged and assure submit is disabled.
        self.wait_for_status('unanswered')
        self.assertFalse(self.problem_page.is_submit_disabled())
        self.problem_page.click_submit()
        self.wait_for_status('incorrect')

    @attr(shard=11)
    def test_cant_submit_blank_answer(self):
        """
        Scenario: I can't submit a blank answer
        When I try to submit blank answer
        Then I can't submit a problem
        """
        if self.can_submit_blank:
            pytest.skip("Test incompatible with the current problem type")

        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )
        self.assertTrue(self.problem_page.is_submit_disabled())

    @attr(shard=12)
    def test_can_show_answer(self):
        """
        Scenario: Verifies that show answer button is working as expected.

        Given that I am on courseware page
        And I can see a CAPA problem with show answer button
        When I click "Show Answer" button
        And I should see question's solution
        And I should see the problem title is focused
        """
        self.problem_page.click_show()
        self.problem_page.wait_for_show_answer_notification()

    @attr(shard=12)
    def test_save_reaction(self):
        """
        Scenario: Verify that the save button performs as expected with problem types

        Given that I am on a problem page
        And I can see a CAPA problem with the Save button present
        When I select and answer and click the "Save" button
        Then I should see the Save notification
        And the Save button should not be disabled
        And clicking on "Review" moves focus to the problem meta area
        And if I change the answer selected
        Then the Save notification should be removed
        """
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )
        self.problem_page.wait_for_page()
        self.answer_problem(correctness='correct')
        self.assertTrue(self.problem_page.is_save_button_enabled())
        self.problem_page.click_save()
        # Ensure "Save" button is enabled after save is complete.
        self.assertTrue(self.problem_page.is_save_button_enabled())
        self.problem_page.wait_for_save_notification()
        # Check that clicking on "Review" goes to the problem meta location
        self.problem_page.click_review_in_notification(notification_type='save')
        self.problem_page.wait_for_focus_on_problem_meta()

        # Not all problems will detect the change and remove the save notification
        if self.can_update_save_notification:
            self.answer_problem(correctness='incorrect')
            self.assertFalse(self.problem_page.is_save_notification_visible())

    @attr(shard=12)
    def test_reset_shows_errors(self):
        """
        Scenario: Reset will show server errors
        If I reset a problem without first answering it
        Then a "gentle notification" is shown
        And the focus moves to the "gentle notification"
        """
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )
        self.wait_for_status('unanswered')
        self.assertFalse(self.problem_page.is_gentle_alert_notification_visible())
        # Click reset without first answering the problem (possible because show_reset_button is set to True)
        self.problem_page.click_reset()
        self.problem_page.wait_for_gentle_alert_notification()

    @attr(shard=12)
    def test_partially_complete_notifications(self):
        """
        Scenario: If a partially correct problem is submitted the correct notification is shown
        If I submit an answer that is partially correct
        Then the partially correct notification should be shown
        """

        # Not all problems have partially correct solutions configured
        if not self.partially_correct:
            pytest.skip("Test incompatible with the current problem type")

        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        self.wait_for_status('unanswered')
        # Set an answer
        self.answer_problem(correctness='partially-correct')
        self.problem_page.click_submit()
        self.problem_page.wait_partial_notification()

    @ddt.data('correct', 'incorrect')
    def test_reset_problem(self, correctness):
        """
        Scenario: I can reset a problem

        Given I am viewing a problem with randomization: always and with reset button: on
        And I answer a problem as <correctness>
        When I reset the problem
        Then my answer is marked "unanswered"
        And The problem displays a "blank" answer
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.problem_page.click_reset()
        self.assertTrue(self.problem_status('unanswered'))


@ddt.ddt
class ChangingAnswerOfProblemTestMixin(object):
    """
    Test the effect of changing the answers of problem
    """

    @ddt.data(['correct', '1/1 point (ungraded)'], ['incorrect', '0/1 point (ungraded)'])
    @ddt.unpack
    def test_checkbox_score_after_answer_and_reset(self, correctness, score):
        """
        Scenario: I can see my score on problem when I answer it and after I reset it

        Given I am viewing problem
        When I answer problem with <correctness>
        Then I should see a <score>
        When I reset the problem
        Then I should see a score of points possible: 0/1 point (ungraded)
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.assertEqual(self.problem_page.problem_progress_graded_value, score)
        self.problem_page.click_reset()
        self.assertEqual(self.problem_page.problem_progress_graded_value, '0/1 point (ungraded)')

    @ddt.data(['correct', 'incorrect'], ['incorrect', 'correct'])
    @ddt.unpack
    def test_reset_correctness_after_changing_answer(self, initial_correctness, other_correctness):
        """
        Scenario: I can reset the correctness of a problem after changing my answer

        Given I am viewing problem
        Then my problem's answer is marked "unanswered"
        When I answer and submit the problem with <initial correctness>
        Then my problem's answer is marked with <initial correctness>
        And I input an answer as <other correctness>
        Then my problem's answer is marked "unanswered"
        """
        self.assertTrue(self.problem_status('unanswered'))
        self.answer_problem(initial_correctness)
        self.problem_page.click_submit()

        self.assertTrue(self.problem_status(initial_correctness))

        self.answer_problem(other_correctness)
        self.assertTrue(self.problem_status('unanswered'))


@ddt.ddt
class NonRandomizedProblemTypeTestMixin(ProblemTypeA11yTestMixin):
    """
    Test the effect of 'randomization: never'
    """
    can_submit_blank = False
    can_update_save_notification = True

    def test_non_randomized_problem_correctly(self):
        """
        Scenario: The reset button doesn't show up

        Given I am viewing a problem with "randomization": never and with "reset button": on
        And I answer problem problem problem correctly
        Then The "Reset" button does not appear
        """
        self.answer_problem("correct")
        self.problem_page.click_submit()
        self.assertFalse(self.problem_page.is_reset_button_present())

    def test_non_randomized_problem_incorrectly(self):
        """
        Scenario: I can reset a non-randomized problem that I answered incorrectly

        Given I am viewing problem with "randomization": never and with "reset button": on
        And I answer problem incorrectly
        When I reset the problem
        Then my problem answer is marked "unanswered"
        And the problem problem displays a "blank" answer
        """
        self.answer_problem("incorrect")
        self.problem_page.click_submit()
        self.problem_page.click_reset()
        self.assertTrue(self.problem_status('unanswered'))


@ddt.ddt
class ProblemNeverShowCorrectnessMixin(object):
    """
    Tests the effect of adding `show_correctness: never` to the sequence metadata
    for subclasses of ProblemTypeTestMixin.
    """
    sequential_metadata = {'show_correctness': 'never'}

    @attr(shard=7)
    @ddt.data('correct', 'incorrect', 'partially-correct')
    def test_answer_says_submitted(self, correctness):
        """
        Scenario: I can answer a problem <Correctness>ly
        Given External graders respond "<Correctness>"
        And I am viewing a "<ProblemType>" problem
        in a subsection with show_correctness set to "never"
        Then I should see a score of "N point(s) possible (ungraded, results hidden)"
        When I answer a "<ProblemType>" problem "<Correctness>ly"
        And the "<ProblemType>" problem displays only a "submitted" notification.
        And I should see a score of "N point(s) possible (ungraded, results hidden)"
        And a "problem_check" server event is emitted
        And a "problem_check" browser event is emitted
        """

        # Not all problems have partially correct solutions configured
        if correctness == 'partially-correct' and not self.partially_correct:
            pytest.skip("Test incompatible with the current problem type")

        # Problem progress text depends on points possible
        possible = 'possible (ungraded, results hidden)'
        if self.problem_points == 1:
            problem_progress = u'1 point {}'.format(possible)
        else:
            problem_progress = u'{} points {}'.format(self.problem_points, possible)

        # Make sure we're looking at the right problem
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        # Learner can see that score will be hidden prior to submitting answer
        self.assertEqual(self.problem_page.problem_progress_graded_value, problem_progress)

        # Answer the problem correctly
        self.answer_problem(correctness=correctness)
        self.problem_page.click_submit()
        self.wait_for_status('submitted')
        self.problem_page.wait_submitted_notification()

        # Score is still hidden after submitting answer
        self.assertEqual(self.problem_page.problem_progress_graded_value, problem_progress)

        # Check for corresponding tracking event
        expected_events = [
            {
                'event_source': 'server',
                'event_type': 'problem_check',
                'username': self.username,
            }, {
                'event_source': 'browser',
                'event_type': 'problem_check',
                'username': self.username,
            },
        ]

        for event in expected_events:
            self.wait_for_events(event_filter=event, number_of_matches=1)


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


class AnnotationProblemTypeTest(AnnotationProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Annotation Problem Type
    """
    shard = 24
    pass


class AnnotationProblemTypeNeverShowCorrectnessTest(AnnotationProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Annotation Problem Type problems.
    """
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
class CheckboxProblemTypeTest(CheckboxProblemTypeBase, ProblemTypeTestMixin, ChangingAnswerOfProblemTestMixin):
    """
    Standard tests for the Checkbox Problem Type
    """
    shard = 24

    def test_can_show_answer(self):
        """
        Scenario: Verifies that show answer button is working as expected.

        Given that I am on courseware page
        And I can see a CAPA problem with show answer button
        When I click "Show Answer" button
        And I should see question's solution
        And I should see correct choices highlighted
        """
        self.problem_page.click_show()
        self.assertTrue(self.problem_page.is_solution_tag_present())
        self.assertTrue(self.problem_page.is_correct_choice_highlighted(correct_choices=[1, 3]))
        self.problem_page.wait_for_show_answer_notification()


class CheckboxProblemTypeTestNonRandomized(CheckboxProblemTypeBase, NonRandomizedProblemTypeTestMixin):
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


class CheckboxProblemTypeNeverShowCorrectnessTest(CheckboxProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Checkbox Problem Type problems.
    """
    pass


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
class MultipleChoiceProblemTypeTest(MultipleChoiceProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Multiple Choice Problem Type
    """
    shard = 24

    def test_can_show_answer(self):
        """
        Scenario: Verifies that show answer button is working as expected.

        Given that I am on courseware page
        And I can see a CAPA problem with show answer button
        When I click "Show Answer" button
        The correct answer is displayed with a single correctness indicator.
        """
        # Click the correct answer, but don't submit yet. No correctness shows.
        self.answer_problem('correct')
        self.assertFalse(self.problem_page.is_correct_choice_highlighted(correct_choices=[3]))

        # After submit, the answer should be marked as correct.
        self.problem_page.click_submit()
        self.assertTrue(self.problem_page.is_correct_choice_highlighted(correct_choices=[3], show_answer=False))

        # Switch to an incorrect answer. This will hide the correctness indicator.
        self.answer_problem('incorrect')
        self.assertFalse(self.problem_page.is_correct_choice_highlighted(correct_choices=[3]))

        # Now click Show Answer. A single correctness indicator should be shown.
        self.problem_page.click_show()
        self.assertTrue(self.problem_page.is_correct_choice_highlighted(correct_choices=[3]))

        # Finally, make sure that clicking Show Answer moved focus to the correct place.
        self.problem_page.wait_for_show_answer_notification()


@ddt.ddt
class MultipleChoiceProblemResetCorrectnessAfterChangingAnswerTest(MultipleChoiceProblemTypeBase):
    """
    Tests for Multiple choice problem with changing answers
    """
    shard = 24

    @ddt.data(['correct', '1/1 point (ungraded)'], ['incorrect', '0/1 point (ungraded)'])
    @ddt.unpack
    def test_mcq_score_after_answer_and_reset(self, correctness, score):
        """
        Scenario: I can see my score on a multiple choice problem when I answer it and after I reset it

        Given I am viewing a multiple choice problem
        When I answer a multiple choice problem <correctness>
        Then I should see a <score>
        When I reset the problem
        Then I should see a score of points possible: 0/1 point (ungraded)
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.assertEqual(self.problem_page.problem_progress_graded_value, score)
        self.problem_page.click_reset()
        self.assertEqual(self.problem_page.problem_progress_graded_value, '0/1 point (ungraded)')

    @ddt.data(['correct', 'incorrect'], ['incorrect', 'correct'])
    @ddt.unpack
    def test_reset_correctness_after_changing_answer(self, initial_correctness, other_correctness):
        """
        Scenario: I can reset the correctness of a multiple choice problem after changing my answer

        Given I am viewing a multiple choice problem
        When I answer a multiple choice problem <initial_correctness>
        Then my multiple choice answer is marked <initial_correctness>
        And I reset the problem
        Then my multiple choice answer is NOT marked <initial_correctness>
        And my multiple choice answer is NOT marked <other_correctness>
        """
        self.assertTrue(self.problem_status("unanswered"))
        self.answer_problem(initial_correctness)
        self.problem_page.click_submit()

        self.assertTrue(self.problem_status(initial_correctness))
        self.problem_page.click_reset()

        self.assertFalse(self.problem_status(initial_correctness))
        self.assertFalse(self.problem_status(other_correctness))


@ddt.ddt
class MultipleChoiceProblemTypeTestNonRandomized(MultipleChoiceProblemTypeBase, NonRandomizedProblemTypeTestMixin):
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

    def test_non_randomized_multiple_choice_with_multiple_attempts(self):
        """
        Scenario: I can answer a problem with multiple attempts correctly but cannot reset because randomization is off

        Given I am viewing a randomization "never" "multiple choice" problem with "3" attempts with reset
        Then I should see "You have used 0 of 3 attempts" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear
        """
        self.assertEqual(
            self.problem_page.submission_feedback,
            "You have used 0 of 3 attempts",
            "All 3 attempts are not available"
        )

        self.answer_problem("correct")
        self.problem_page.click_submit()
        self.assertFalse(self.problem_page.is_reset_button_present())


class MultipleChoiceProblemTypeTestOneAttempt(MultipleChoiceProblemTypeBase):
    """
    Test Multiple choice problem with single attempt
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
            metadata={'rerandomize': 'never', 'show_reset_button': True, 'max_attempts': 1}
        )

    def test_answer_with_one_attempt_correctly(self):
        """
        Scenario: I can answer a problem with one attempt correctly and can not reset

        Given I am viewing a "multiple choice" problem with "1" attempt
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear
        """
        self.answer_problem("correct")
        self.problem_page.click_submit()
        self.assertFalse(self.problem_page.is_reset_button_present())


class MultipleChoiceProblemTypeTestMultipleAttempt(MultipleChoiceProblemTypeBase):
    """
    Test Multiple choice problem with multiple attempts
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
            metadata={'rerandomize': 'always', 'show_reset_button': True, 'max_attempts': 3}
        )

    def test_answer_with_multiple_attempt_correctly(self):
        """
        Scenario: I can answer a problem with multiple attempts correctly and still reset the problem

        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 attempts" somewhere in the page
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does appear
        """
        self.assertEqual(
            self.problem_page.submission_feedback,
            "You have used 0 of 3 attempts",
            "All 3 attempts are not available"
        )
        self.answer_problem("correct")
        self.problem_page.click_submit()
        self.assertTrue(self.problem_page.is_reset_button_present())

    def test_learner_can_see_attempts_left(self):
        """
        Scenario: I can view how many attempts I have left on a problem

        Given I am viewing a "multiple choice" problem with "3" attempts
        Then I should see "You have used 0 of 3 attempts" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        And I reset the problem
        Then I should see "You have used 1 of 3 attempts" somewhere in the page
        When I answer a "multiple choice" problem "incorrectly"
        And I reset the problem
        Then I should see "You have used 2 of 3 attempts" somewhere in the page
        And The "Submit" button does appear
        When I answer a "multiple choice" problem "correctly"
        Then The "Reset" button does not appear
        """
        for attempts_used in range(3):
            self.assertEqual(
                self.problem_page.submission_feedback,
                u"You have used {} of 3 attempts".format(str(attempts_used)),
                "All 3 attempts are not available"
            )
            if attempts_used == 2:
                self.assertTrue(self.problem_page.is_submit_disabled())
                self.answer_problem("correct")
                self.problem_page.click_submit()
                self.assertFalse(self.problem_page.is_reset_button_present())
            else:
                self.answer_problem("incorrect")
                self.problem_page.click_submit()
                self.problem_page.click_reset()


class MultipleChoiceProblemTypeNeverShowCorrectnessTest(MultipleChoiceProblemTypeBase,
                                                        ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Multiple Choice Problem Type problems.
    """
    pass


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
class RadioProblemTypeTest(RadioProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Multiple Radio Problem Type
    """
    shard = 24
    pass


@ddt.ddt
class RadioProblemResetCorrectnessAfterChangingAnswerTest(RadioProblemTypeBase):
    """
    Tests for Radio problem with changing answers
    """
    shard = 24

    @ddt.data(['correct', '1/1 point (ungraded)'], ['incorrect', '0/1 point (ungraded)'])
    @ddt.unpack
    def test_radio_score_after_answer_and_reset(self, correctness, score):
        """
        Scenario: I can see my score on a radio problem when I answer it and after I reset it

        Given I am viewing a radio problem
        When I answer a radio problem <correctness>
        Then I should see a <score>
        When I reset the problem
        Then I should see a score of points possible: 0/1 point (ungraded)
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.assertEqual(self.problem_page.problem_progress_graded_value, score)
        self.problem_page.click_reset()
        self.assertEqual(self.problem_page.problem_progress_graded_value, '0/1 point (ungraded)')

    @ddt.data(['correct', 'incorrect'], ['incorrect', 'correct'])
    @ddt.unpack
    def test_reset_correctness_after_changing_answer(self, initial_correctness, other_correctness):
        """
        Scenario: I can reset the correctness of a radio problem after changing my answer

        Given I am viewing a radio problem
        When I answer a radio problem with <initial_correctness>
        Then my radio answer is marked <initial_correctness>
        And I reset the problem
        Then my radio problem's answer is NOT marked <initial_correctness>
        And my radio problem's answer is NOT marked <other_correctness>
        """
        self.assertTrue(self.problem_status("unanswered"))
        self.answer_problem(initial_correctness)
        self.problem_page.click_submit()

        self.assertTrue(self.problem_status(initial_correctness))
        self.problem_page.click_reset()

        self.assertFalse(self.problem_status(initial_correctness))
        self.assertFalse(self.problem_status(other_correctness))


class RadioProblemTypeTestNonRandomized(RadioProblemTypeBase, NonRandomizedProblemTypeTestMixin):
    """
    Tests for non-randomized radio problem
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


class RadioProblemTypeNeverShowCorrectnessTest(RadioProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Radio Problem Type problems.
    """
    pass


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
class DropdownProblemTypeTest(DropDownProblemTypeBase, ProblemTypeTestMixin, ChangingAnswerOfProblemTestMixin):
    """
    Standard tests for the Dropdown Problem Type
    """
    shard = 24
    pass


@ddt.ddt
class DropDownProblemTypeTestNonRandomized(DropDownProblemTypeBase, NonRandomizedProblemTypeTestMixin):
    """
    Tests for non-randomized Dropdown problem
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


class DropDownProblemTypeNeverShowCorrectnessTest(DropDownProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Drop Down Problem Type problems.
    """
    pass


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


class StringProblemTypeTest(StringProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the String Problem Type
    """
    shard = 24
    pass


class StringProblemTypeNeverShowCorrectnessTest(StringProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for String Problem Type problems.
    """
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
class NumericalProblemTypeTest(NumericalProblemTypeBase, ProblemTypeTestMixin, ChangingAnswerOfProblemTestMixin):
    """
    Standard tests for the Numerical Problem Type
    """
    shard = 12

    def test_error_input_gentle_alert(self):
        """
        Scenario: I can answer a problem with erroneous input and will see a gentle alert
        Given a Numerical Problem type
        I can input a string answer
        Then I will see a Gentle alert notification
        And focus will shift to that notification
        And clicking on "Review" moves focus to the problem meta area
        """
        # Make sure we're looking at the right problem
        self.problem_page.wait_for(
            lambda: self.problem_page.problem_name == self.problem_name,
            "Make sure the correct problem is on the page"
        )

        # Answer the problem with an erroneous input to cause a gentle alert
        self.assertFalse(self.problem_page.is_gentle_alert_notification_visible())
        self.answer_problem(correctness='error')
        self.problem_page.click_submit()
        self.problem_page.wait_for_gentle_alert_notification()
        # Check that clicking on "Review" goes to the problem meta location
        self.problem_page.click_review_in_notification(notification_type='gentle-alert')
        self.problem_page.wait_for_focus_on_problem_meta()


@ddt.ddt
class NumericalProblemTypeTestNonRandomized(NumericalProblemTypeBase, NonRandomizedProblemTypeTestMixin):
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


class NumericalProblemTypeTestViewAnswer(NumericalProblemTypeBase):
    """
    Test learner can view Numerical problem's answer
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
            metadata={'showanswer': 'always'}
        )

    def test_learner_can_view_answer(self):
        """
        Scenario: I can view the answer if the problem has it:

        Given I am viewing a "numerical" that shows the answer "always"
        When I press the button with the label "Show Answer"
        And I should see "4.14159" somewhere in the page
        """
        self.problem_page.click_show()
        self.assertEqual(self.problem_page.answer, '4.14159')


class NumericalProblemTypeNeverShowCorrectnessTest(NumericalProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Numerical Problem Type problems.
    """
    pass


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
class FormulaProblemTypeTest(FormulaProblemTypeBase, ProblemTypeTestMixin, ChangingAnswerOfProblemTestMixin):
    """
    Standard tests for the Formula Problem Type
    """
    shard = 24
    pass


class FormulaProblemTypeTestNonRandomized(FormulaProblemTypeBase, NonRandomizedProblemTypeTestMixin):
    """
    Tests for non-randomized Formula problem
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


class FormulaProblemTypeNeverShowCorrectnessTest(FormulaProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Formula Problem Type problems.
    """
    pass


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
class ScriptProblemTypeTest(ScriptProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Script Problem Type
    """
    shard = 24
    pass


@ddt.ddt
class ScriptProblemResetAfterAnswerTest(ScriptProblemTypeBase):
    """
    Test Script problem by resetting answers
    """
    shard = 24

    @ddt.data(['correct', 'incorrect'], ['incorrect', 'correct'])
    @ddt.unpack
    def test_reset_correctness_after_changing_answer(self, initial_correctness, other_correctness):
        """
        Scenario: I can reset the correctness of a problem after changing my answer

        Given I am viewing a script problem
        Then my script problem's answer is marked "unanswered"
        When I answer a script problem initial correctness
        And I input an answer on a script problem other correctness
        Then my script problem answer is marked "unanswered"
        """
        self.assertTrue(self.problem_status('unanswered'))
        self.answer_problem(initial_correctness)
        self.problem_page.click_submit()

        self.assertTrue(self.problem_status(initial_correctness))

        self.answer_problem(other_correctness)
        self.assertTrue(self.problem_status('unanswered'))

    @ddt.data(['correct', '2/2 points (ungraded)'], ['incorrect', '0/2 points (ungraded)'])
    @ddt.unpack
    def test_script_score_after_answer_and_reset(self, correctness, score):
        """
        Scenario: I can see my score on a script problem when I answer it and after I reset it

        Given I am viewing a script problem
        When I answer a script problem correct/incorrect
        Then I should see a score
        When I reset the problem
        Then I should see a score of points possible: 0/2 points (ungraded)
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.assertEqual(self.problem_page.problem_progress_graded_value, score)
        self.problem_page.click_reset()
        self.assertEqual(self.problem_page.problem_progress_graded_value, '0/2 points (ungraded)')


class ScriptProblemTypeTestNonRandomized(ScriptProblemTypeBase, NonRandomizedProblemTypeTestMixin):
    """
    Tests for non-randomized Script problem
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


class ScriptProblemTypeNeverShowCorrectnessTest(ScriptProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Script Problem Type problems.
    """
    pass


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


class CodeProblemTypeTest(CodeProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Code Problem Type
    """
    shard = 12

    def test_answer_incorrectly(self):
        """
        Overridden for script test because the testing grader always responds
        with "correct"
        """
        pass

    def test_submit_blank_answer(self):
        """
        Overridden for script test because the testing grader always responds
        with "correct"
        """
        pass

    def test_cant_submit_blank_answer(self):
        """
        Overridden for script test because the testing grader always responds
        with "correct"
        """
        pass

    def wait_for_status(self, status):
        """
        Overridden for script test because the testing grader always responds
        with "correct"
        """
        pass


class CodeProblemTypeNeverShowCorrectnessTest(CodeProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Code Problem Type problems.
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
class RadioTextProblemTypeTest(RadioTextProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Radio Text Problem Type
    """
    shard = 24
    pass


@ddt.ddt
class RadioTextProblemResetCorrectnessAfterChangingAnswerTest(RadioTextProblemTypeBase):
    """
    Tests for Radio Text problem with changing answers
    """
    shard = 24

    @ddt.data(['correct', '1/1 point (ungraded)'], ['incorrect', '0/1 point (ungraded)'])
    @ddt.unpack
    def test_mcq_score_after_answer_and_reset(self, correctness, score):
        """
        Scenario: I can see my score on a radio text problem when I answer it and after I reset it

        Given I am viewing a radio text problem
        When I answer a radio text problem correct/incorrect
        Then I should see a score
        When I reset the problem
        Then I should see a score of points possible: (1/1 point (ungraded) -- 0/1 point (ungraded)
        """
        self.answer_problem(correctness)
        self.problem_page.click_submit()
        self.assertEqual(self.problem_page.problem_progress_graded_value, score)
        self.problem_page.click_reset()
        self.assertEqual(self.problem_page.problem_progress_graded_value, '0/1 point (ungraded)')

    @ddt.data(['correct', 'incorrect'], ['incorrect', 'correct'])
    @ddt.unpack
    def test_reset_correctness_after_changing_answer(self, initial_correctness, other_correctness):
        """
        Scenario: I can reset the correctness of a multiple choice problem after changing my answer

        Given I am viewing a radio text problem
        When I answer a radio text problem InitialCorrectness
        Then my radio text answer is marked InitialCorrectness
        And I reset the problem
        Then my answer is NOT marked InitialCorrectness
        And my answer is NOT marked OtherCorrectness
        """
        self.assertTrue(self.problem_status("unanswered"))
        self.answer_problem(initial_correctness)
        self.problem_page.click_submit()

        self.assertTrue(self.problem_status(initial_correctness))
        self.problem_page.click_reset()

        self.assertFalse(self.problem_status(initial_correctness))
        self.assertFalse(self.problem_status(other_correctness))


class RadioTextProblemTypeTestNonRandomized(RadioTextProblemTypeBase, NonRandomizedProblemTypeTestMixin):
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


class RadioTextProblemTypeNeverShowCorrectnessTest(RadioTextProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Radio + Text Problem Type problems.
    """
    pass


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


class CheckboxTextProblemTypeTest(CheckboxTextProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Checkbox Text Problem Type
    """
    pass


class CheckboxTextProblemTypeTestNonRandomized(CheckboxTextProblemTypeBase, NonRandomizedProblemTypeTestMixin):
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


class CheckboxTextProblemTypeNeverShowCorrectnessTest(CheckboxTextProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Checkbox + Text Problem Type problems.
    """
    pass


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


class SymbolicProblemTypeTest(SymbolicProblemTypeBase, ProblemTypeTestMixin):
    """
    Standard tests for the Symbolic Problem Type
    """
    pass


class SymbolicProblemTypeNeverShowCorrectnessTest(SymbolicProblemTypeBase, ProblemNeverShowCorrectnessMixin):
    """
    Ensure that correctness can be withheld for Symbolic Problem Type problems.
    """
    pass
