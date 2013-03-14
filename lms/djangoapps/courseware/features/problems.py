from lettuce import world, step
from lettuce.django import django_url
from selenium.webdriver.support.ui import Select
import random
from common import i_am_registered_for_the_course

@step(u'I am viewing a "([^"]*)" problem')
def view_problem(step, problem_type):
    i_am_registered_for_the_course(step, 'edX/model_course/2013_Spring')
    url = django_url(problem_url(problem_type))
    world.browser.visit(url)

@step(u'I answer a "([^"]*)" problem "([^"]*)ly"')
def answer_problem(step, problem_type, correctness):
    """ Mark a given problem type correct or incorrect, then submit it.

    *problem_type* is a string representing the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect']
    """

    assert(correctness in ['correct', 'incorrect'])

    if problem_type == "drop down":
        select_name = "input_i4x-edX-model_course-problem-Drop_Down_Problem_2_1"
        option_text = 'Option 2' if correctness == 'correct' else 'Option 3'
        world.browser.select(select_name, option_text)

    elif problem_type == "multiple choice":
        if correctness == 'correct':
            inputfield('multiple choice', choice='choice_3').check()
        else:
            inputfield('multiple choice', choice='choice_2').check()

    elif problem_type == "checkbox":
        if correctness == 'correct':
            inputfield('checkbox', choice='choice_0').check()
            inputfield('checkbox', choice='choice_2').check()
        else:
            inputfield('checkbox', choice='choice_3').check()

    elif problem_type == 'string':
        textvalue = 'correct string' if correctness == 'correct' else 'incorrect'
        inputfield('string').fill(textvalue)

    elif problem_type == 'numerical':
        textvalue = "pi + 1" if correctness == 'correct' else str(random.randint(-2,2))
        inputfield('numerical').fill(textvalue)

    elif problem_type == 'formula':
        textvalue = "x^2+2*x+y" if correctness == 'correct' else 'x^2'
        inputfield('formula').fill(textvalue)

    # Submit the problem
    check_problem(step)

@step(u'I check a problem')
def check_problem(step):
    world.browser.find_by_css("input.check").click()

@step(u'I reset the problem')
def reset_problem(step):
    world.browser.find_by_css('input.reset').click()

@step(u'My "([^"]*)" answer is marked "([^"]*)"')
def assert_answer_mark(step, problem_type, correctness):
    """ Assert that the expected answer mark is visible for a given problem type.

    *problem_type* is a string identifying the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect', 'unanswered']

    Asserting that a problem is marked 'unanswered' means that
    the problem is NOT marked correct and NOT marked incorrect.
    This can occur, for example, if the user has reset the problem.  """

    # Dictionaries that map problem types to the css selectors
    # for correct/incorrect marks.  
    # The elements are lists of selectors because a particular problem type
    # might be marked in multiple ways.  
    # For example, multiple choice is marked incorrect differently 
    # depending on whether the user selects an incorrect 
    # item or submits without selecting any item)
    correct_selectors = { 'drop down': ['span.correct'],
                           'multiple choice': ['label.choicegroup_correct'],
                            'checkbox': ['span.correct'],
                            'string': ['div.correct'],
                            'numerical': ['div.correct'],
                            'formula': ['div.correct'], }

    incorrect_selectors = { 'drop down': ['span.incorrect'],
                           'multiple choice': ['label.choicegroup_incorrect', 
                                                'span.incorrect'],
                            'checkbox': ['span.incorrect'],
                            'string': ['div.incorrect'],
                            'numerical': ['div.incorrect'],
                            'formula': ['div.incorrect'], }

    assert(correctness in ['correct', 'incorrect', 'unanswered'])
    assert(problem_type in correct_selectors and problem_type in incorrect_selectors)

    # Assert that the question has the expected mark
    # (either correct or incorrect)
    if correctness in ["correct", "incorrect"]:

        selector_dict = correct_selectors if correctness == "correct" else incorrect_selectors

        # At least one of the correct selectors should be present
        for sel in selector_dict[problem_type]:
            has_expected_mark = world.browser.is_element_present_by_css(sel, wait_time=4)

            # As soon as we find the selector, break out of the loop
            if has_expected_mark:
                break

        # Expect that we found the right mark (correct or incorrect)
        assert(has_expected_mark)

    # Assert that the question has neither correct nor incorrect
    # because it is unanswered (possibly reset)
    else:
        # Get all the correct/incorrect selectors for this problem type
        selector_list = correct_selectors[problem_type] + incorrect_selectors[problem_type]

        # Assert that none of the correct/incorrect selectors are present
        for sel in selector_list:
            assert(world.browser.is_element_not_present_by_css(sel, wait_time=4))


def problem_url(problem_type):
    """ Construct a url to a page with the given problem type """
    base = '/courses/edX/model_course/2013_Spring/courseware/Problem_Components/'
    url_extensions = { 'drop down': 'Drop_Down_Problems',
                   'multiple choice': 'Multiple_Choice_Problems',
                    'checkbox': 'Checkbox_Problems', 
                    'string': 'String_Problems',
                    'numerical': 'Numerical_Problems', 
                    'formula': 'Formula_Problems', }

    assert(problem_type in url_extensions)
    return base + url_extensions[problem_type]



def inputfield(problem_type, choice=None):
    """ Return the <input> element for *problem_type*.
    For example, if problem_type is 'string', return
    the text field for the string problem in the test course.

    *choice* is the name of the checkbox input in a group
    of checkboxes. """

    field_extensions = { 'drop down': 'Drop_Down_Problem',
                           'multiple choice': 'Multiple_Choice_Problem',
                            'checkbox': 'Checkbox_Problem', 
                            'string': 'String_Problem',
                            'numerical': 'Numerical_Problem', 
                            'formula': 'Formula_Problem', }

    assert(problem_type in field_extensions)
    extension = field_extensions[problem_type]
    sel = "input#input_i4x-edX-model_course-problem-%s_2_1" % extension

    if choice is not None:
        base = "_choice_" if problem_type == "multiple choice" else "_"
        sel = sel + base + str(choice)

    return world.browser.find_by_css(sel)
