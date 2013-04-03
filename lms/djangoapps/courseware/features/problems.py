'''
Steps for problem.feature lettuce tests
'''

#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
import random
import textwrap
from common import i_am_registered_for_the_course, \
                TEST_SECTION_NAME, section_location
from capa.tests.response_xml_factory import OptionResponseXMLFactory, \
    ChoiceResponseXMLFactory, MultipleChoiceResponseXMLFactory, \
    StringResponseXMLFactory, NumericalResponseXMLFactory, \
    FormulaResponseXMLFactory, CustomResponseXMLFactory, \
    CodeResponseXMLFactory

# Factories from capa.tests.response_xml_factory that we will use
# to generate the problem XML, with the keyword args used to configure
# the output.
PROBLEM_FACTORY_DICT = {
    'drop down': {
        'factory': OptionResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The correct answer is Option 2',
            'options': ['Option 1', 'Option 2', 'Option 3', 'Option 4'],
            'correct_option': 'Option 2'}},

    'multiple choice': {
        'factory': MultipleChoiceResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The correct answer is Choice 3',
            'choices': [False, False, True, False],
            'choice_names': ['choice_0', 'choice_1', 'choice_2', 'choice_3']}},

    'checkbox': {
        'factory': ChoiceResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The correct answer is Choices 1 and 3',
            'choice_type': 'checkbox',
            'choices': [True, False, True, False, False],
            'choice_names': ['Choice 1', 'Choice 2', 'Choice 3', 'Choice 4']}},

    'string': {
        'factory': StringResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The answer is "correct string"',
            'case_sensitive': False,
            'answer': 'correct string'}},

    'numerical': {
        'factory': NumericalResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The answer is pi + 1',
            'answer': '4.14159',
            'tolerance': '0.00001',
            'math_display': True}},

    'formula': {
        'factory': FormulaResponseXMLFactory(),
        'kwargs': {
            'question_text': 'The solution is [mathjax]x^2+2x+y[/mathjax]',
            'sample_dict': {'x': (-100, 100), 'y': (-100, 100)},
            'num_samples': 10,
            'tolerance': 0.00001,
            'math_display': True,
            'answer': 'x^2+2*x+y'}},

    'script': {
        'factory': CustomResponseXMLFactory(),
        'kwargs': {
            'question_text': 'Enter two integers that sum to 10.',
            'cfn': 'test_add_to_ten',
            'expect': '10',
            'num_inputs': 2,
            'script': textwrap.dedent("""
                def test_add_to_ten(expect,ans):
                    try:
                        a1=int(ans[0])
                        a2=int(ans[1])
                    except ValueError:
                        a1=0
                        a2=0
                    return (a1+a2)==int(expect)
            """)}},
    'code': {
        'factory': CodeResponseXMLFactory(),
        'kwargs': {
            'question_text': 'Submit code to an external grader',
            'initial_display': 'print "Hello world!"',
            'grader_payload': '{"grader": "ps1/Spring2013/test_grader.py"}', }},
       }


def add_problem_to_course(course, problem_type):
    '''
    Add a problem to the course we have created using factories.
    '''

    assert(problem_type in PROBLEM_FACTORY_DICT)

    # Generate the problem XML using capa.tests.response_xml_factory
    factory_dict = PROBLEM_FACTORY_DICT[problem_type]
    problem_xml = factory_dict['factory'].build_xml(**factory_dict['kwargs'])

    # Create a problem item using our generated XML
    # We set rerandomize=always in the metadata so that the "Reset" button
    # will appear.
    template_name = "i4x://edx/templates/problem/Blank_Common_Problem"
    world.ItemFactory.create(parent_location=section_location(course),
                            template=template_name,
                            display_name=str(problem_type),
                            data=problem_xml,
                            metadata={'rerandomize': 'always'})


@step(u'I am viewing a "([^"]*)" problem')
def view_problem(step, problem_type):
    i_am_registered_for_the_course(step, 'model_course')

    # Ensure that the course has this problem type
    add_problem_to_course('model_course', problem_type)

    # Go to the one section in the factory-created course
    # which should be loaded with the correct problem
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


@step(u'External graders respond "([^"]*)"')
def set_external_grader_response(step, correctness):
    assert(correctness in ['correct', 'incorrect'])

    response_dict = {'correct': True if correctness == 'correct' else False,
                    'score': 1 if correctness == 'correct' else 0,
                    'msg': 'Your problem was graded %s' % correctness}

    # Set the fake xqueue server to always respond
    # correct/incorrect when asked to grade a problem
    world.xqueue_server.set_grade_response(response_dict)


@step(u'I answer a "([^"]*)" problem "([^"]*)ly"')
def answer_problem(step, problem_type, correctness):
    """ Mark a given problem type correct or incorrect, then submit it.

    *problem_type* is a string representing the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect']
    """

    assert(correctness in ['correct', 'incorrect'])

    if problem_type == "drop down":
        select_name = "input_i4x-edx-model_course-problem-drop_down_2_1"
        option_text = 'Option 2' if correctness == 'correct' else 'Option 3'
        world.browser.select(select_name, option_text)

    elif problem_type == "multiple choice":
        if correctness == 'correct':
            inputfield('multiple choice', choice='choice_2').check()
        else:
            inputfield('multiple choice', choice='choice_1').check()

    elif problem_type == "checkbox":
        if correctness == 'correct':
            inputfield('checkbox', choice='choice_0').check()
            inputfield('checkbox', choice='choice_2').check()
        else:
            inputfield('checkbox', choice='choice_3').check()

    elif problem_type == 'string':
        textvalue = 'correct string' if correctness == 'correct' \
                                    else 'incorrect'
        inputfield('string').fill(textvalue)

    elif problem_type == 'numerical':
        textvalue = "pi + 1" if correctness == 'correct' \
                            else str(random.randint(-2, 2))
        inputfield('numerical').fill(textvalue)

    elif problem_type == 'formula':
        textvalue = "x^2+2*x+y" if correctness == 'correct' else 'x^2'
        inputfield('formula').fill(textvalue)

    elif problem_type == 'script':
        # Correct answer is any two integers that sum to 10
        first_addend = random.randint(-100, 100)
        second_addend = 10 - first_addend

        # If we want an incorrect answer, then change
        # the second addend so they no longer sum to 10
        if correctness == 'incorrect':
            second_addend += random.randint(1, 10)

        inputfield('script', input_num=1).fill(str(first_addend))
        inputfield('script', input_num=2).fill(str(second_addend))

    elif problem_type == 'code':
        # The fake xqueue server is configured to respond
        # correct / incorrect no matter what we submit.
        # Furthermore, since the inline code response uses
        # JavaScript to make the code display nicely, it's difficult
        # to programatically input text
        # (there's not <textarea> we can just fill text into)
        # For this reason, we submit the initial code in the response
        # (configured in the problem XML above)
        pass

    # Submit the problem
    check_problem(step)


@step(u'The "([^"]*)" problem displays a "([^"]*)" answer')
def assert_problem_has_answer(step, problem_type, answer_class):
    '''
    Assert that the problem is displaying a particular answer.
    These correspond to the same correct/incorrect
    answers we set in answer_problem()

    We can also check that a problem has been left blank
    by setting answer_class='blank'
    '''
    assert answer_class in ['correct', 'incorrect', 'blank']

    if problem_type == "drop down":
        if answer_class == 'blank':
            assert world.browser.is_element_not_present_by_css('option[selected="true"]')
        else:
            actual = world.browser.find_by_css('option[selected="true"]').value
            expected = 'Option 2' if answer_class == 'correct' else 'Option 3'
            assert actual == expected

    elif problem_type == "multiple choice":
        if answer_class == 'correct':
            assert_checked('multiple choice', ['choice_2'])
        elif answer_class == 'incorrect':
            assert_checked('multiple choice', ['choice_1'])
        else:
            assert_checked('multiple choice', [])

    elif problem_type == "checkbox":
        if answer_class == 'correct':
            assert_checked('checkbox', ['choice_0', 'choice_2'])
        elif answer_class == 'incorrect':
            assert_checked('checkbox', ['choice_3'])
        else:
            assert_checked('checkbox', [])

    elif problem_type == 'string':
        if answer_class == 'blank':
            expected = ''
        else:
            expected = 'correct string' if answer_class == 'correct' \
                                        else 'incorrect'

        assert_textfield('string', expected)

    elif problem_type == 'formula':
        if answer_class == 'blank':
            expected = ''
        else:
            expected = "x^2+2*x+y" if answer_class == 'correct' else 'x^2'

        assert_textfield('formula', expected)

    else:
        # The other response types use random data,
        # which would be difficult to check
        # We trade input value coverage in the other tests for
        # input type coverage in this test.
        pass


@step(u'I check a problem')
def check_problem(step):
    world.css_click("input.check")


@step(u'I reset the problem')
def reset_problem(step):
    world.css_click('input.reset')


# Dictionaries that map problem types to the css selectors
# for correct/incorrect/unanswered marks.
# The elements are lists of selectors because a particular problem type
# might be marked in multiple ways.
# For example, multiple choice is marked incorrect differently
# depending on whether the user selects an incorrect
# item or submits without selecting any item)
CORRECTNESS_SELECTORS = {
        'correct': {'drop down': ['span.correct'],
                       'multiple choice': ['label.choicegroup_correct'],
                        'checkbox': ['span.correct'],
                        'string': ['div.correct'],
                        'numerical': ['div.correct'],
                        'formula': ['div.correct'],
                        'script': ['div.correct'],
                        'code': ['span.correct']},

        'incorrect': {'drop down': ['span.incorrect'],
                       'multiple choice': ['label.choicegroup_incorrect',
                                            'span.incorrect'],
                        'checkbox': ['span.incorrect'],
                        'string': ['div.incorrect'],
                        'numerical': ['div.incorrect'],
                        'formula': ['div.incorrect'],
                        'script': ['div.incorrect'],
                        'code': ['span.incorrect']},

        'unanswered': {'drop down': ['span.unanswered'],
                       'multiple choice': ['span.unanswered'],
                        'checkbox': ['span.unanswered'],
                        'string': ['div.unanswered'],
                        'numerical': ['div.unanswered'],
                        'formula': ['div.unanswered'],
                        'script': ['div.unanswered'],
                        'code': ['span.unanswered']}}


@step(u'My "([^"]*)" answer is marked "([^"]*)"')
def assert_answer_mark(step, problem_type, correctness):
    """
    Assert that the expected answer mark is visible
    for a given problem type.

    *problem_type* is a string identifying the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect', 'unanswered']
    """

    # Determine which selector(s) to look for based on correctness
    assert(correctness in CORRECTNESS_SELECTORS)
    selector_dict = CORRECTNESS_SELECTORS[correctness]
    assert(problem_type in selector_dict)

    # At least one of the correct selectors should be present
    for sel in selector_dict[problem_type]:
        has_expected = world.is_css_present(sel)

        # As soon as we find the selector, break out of the loop
        if has_expected:
            break

    # Expect that we found the expected selector
    assert(has_expected)


def inputfield(problem_type, choice=None, input_num=1):
    """ Return the <input> element for *problem_type*.
    For example, if problem_type is 'string', return
    the text field for the string problem in the test course.

    *choice* is the name of the checkbox input in a group
    of checkboxes. """

    sel = ("input#input_i4x-edx-model_course-problem-%s_2_%s" %
           (problem_type.replace(" ", "_"), str(input_num)))

    if choice is not None:
        base = "_choice_" if problem_type == "multiple choice" else "_"
        sel = sel + base + str(choice)


    # If the input element doesn't exist, fail immediately
    assert world.is_css_present(sel)

    # Retrieve the input element
    return world.browser.find_by_css(sel)


def assert_checked(problem_type, choices):
    '''
    Assert that choice names given in *choices* are the only
    ones checked.

    Works for both radio and checkbox problems
    '''

    all_choices = ['choice_0', 'choice_1', 'choice_2', 'choice_3']
    for this_choice in all_choices:
        element = inputfield(problem_type, choice=this_choice)

        if this_choice in choices:
            assert element.checked
        else:
            assert not element.checked


def assert_textfield(problem_type, expected_text, input_num=1):
    element = inputfield(problem_type, input_num=input_num)
    assert element.value == expected_text
