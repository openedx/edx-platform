'''
Steps for problem.feature lettuce tests
'''

#pylint: disable=C0111
#pylint: disable=W0621

from lettuce import world, step
from lettuce.django import django_url
from common import i_am_registered_for_the_course, TEST_SECTION_NAME
from problems_setup import PROBLEM_DICT, answer_problem, problem_has_answer, add_problem_to_course
from nose.tools import assert_equal


@step(u'I am viewing a "([^"]*)" problem with "([^"]*)" attempt')
def view_problem_with_attempts(step, problem_type, attempts):
    i_am_registered_for_the_course(step, 'model_course')

    # Ensure that the course has this problem type
    add_problem_to_course('model_course', problem_type, {'attempts': attempts})

    # Go to the one section in the factory-created course
    # which should be loaded with the correct problem
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


@step(u'I am viewing a "([^"]*)" that shows the answer "([^"]*)"')
def view_problem_with_show_answer(step, problem_type, answer):
    i_am_registered_for_the_course(step, 'model_course')

    # Ensure that the course has this problem type
    add_problem_to_course('model_course', problem_type, {'showanswer': answer})

    # Go to the one section in the factory-created course
    # which should be loaded with the correct problem
    chapter_name = TEST_SECTION_NAME.replace(" ", "_")
    section_name = chapter_name
    url = django_url('/courses/edx/model_course/Test_Course/courseware/%s/%s' %
                    (chapter_name, section_name))

    world.browser.visit(url)


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
def answer_problem_step(step, problem_type, correctness):
    """ Mark a given problem type correct or incorrect, then submit it.

    *problem_type* is a string representing the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect']
    """

    assert(correctness in ['correct', 'incorrect'])
    assert(problem_type in PROBLEM_DICT)
    answer_problem(problem_type, correctness)

    # Submit the problem
    check_problem(step)


@step(u'I check a problem')
def check_problem(step):
    world.css_click("input.check")


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
    assert problem_type in PROBLEM_DICT
    problem_has_answer(problem_type, answer_class)


@step(u'I reset the problem')
def reset_problem(_step):
    world.css_click('input.reset')


@step(u'I press the button with the label "([^"]*)"$')
def press_the_button_with_label(_step, buttonname):
    button_css = 'button span.show-label'
    elem = world.css_find(button_css).first
    assert_equal(elem.text, buttonname)
    world.css_click(button_css)


@step(u'The "([^"]*)" button does( not)? appear')
def action_button_present(_step, buttonname, doesnt_appear):
    button_css = 'section.action input[value*="%s"]' % buttonname
    if doesnt_appear:
        assert world.is_css_not_present(button_css)
    else:
        assert world.is_css_present(button_css)


@step(u'the button with the label "([^"]*)" does( not)? appear')
def button_with_label_present(step, buttonname, doesnt_appear):
    if doesnt_appear:
        assert world.browser.is_text_not_present(buttonname, wait_time=5)
    else:
        assert world.browser.is_text_present(buttonname, wait_time=5)


@step(u'My "([^"]*)" answer is marked "([^"]*)"')
def assert_answer_mark(step, problem_type, correctness):
    """
    Assert that the expected answer mark is visible
    for a given problem type.

    *problem_type* is a string identifying the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect', 'unanswered']
    """

    # Determine which selector(s) to look for based on correctness
    assert(correctness in ['correct', 'incorrect', 'unanswered'])
    assert(problem_type in PROBLEM_DICT)

    # At least one of the correct selectors should be present
    for sel in PROBLEM_DICT[problem_type][correctness]:
        has_expected = world.is_css_present(sel)

        # As soon as we find the selector, break out of the loop
        if has_expected:
            break

    # Expect that we found the expected selector
    assert(has_expected)
