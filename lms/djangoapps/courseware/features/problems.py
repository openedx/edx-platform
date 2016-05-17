'''
Steps for problem.feature lettuce tests
'''

# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from common import i_am_registered_for_the_course, visit_scenario_item
from problems_setup import PROBLEM_DICT, answer_problem, problem_has_answer, add_problem_to_course


def _view_problem(step, problem_type, problem_settings=None):
    i_am_registered_for_the_course(step, 'model_course')

    # Ensure that the course has this problem type
    add_problem_to_course(world.scenario_dict['COURSE'].number, problem_type, problem_settings)

    # Go to the one section in the factory-created course
    # which should be loaded with the correct problem
    visit_scenario_item('SECTION')


@step(u'I am viewing a "([^"]*)" problem with "([^"]*)" attempt')
def view_problem_with_attempts(step, problem_type, attempts):
    _view_problem(step, problem_type, {'max_attempts': attempts})


@step(u'I am viewing a randomization "([^"]*)" "([^"]*)" problem with "([^"]*)" attempts with reset')
def view_problem_attempts_reset(step, randomization, problem_type, attempts, ):
    _view_problem(step, problem_type, {'max_attempts': attempts,
                                       'rerandomize': randomization,
                                       'show_reset_button': True})


@step(u'I am viewing a "([^"]*)" that shows the answer "([^"]*)"')
def view_problem_with_show_answer(step, problem_type, answer):
    _view_problem(step, problem_type, {'showanswer': answer})


@step(u'I am viewing a "([^"]*)" problem')
def view_problem(step, problem_type):
    _view_problem(step, problem_type)


@step(u'I am viewing a randomization "([^"]*)" "([^"]*)" problem with reset button on')
def view_random_reset_problem(step, randomization, problem_type):
    _view_problem(step, problem_type, {'rerandomize': randomization, 'show_reset_button': True})


@step(u'External graders respond "([^"]*)"')
def set_external_grader_response(step, correctness):
    assert(correctness in ['correct', 'incorrect'])

    response_dict = {
        'correct': True if correctness == 'correct' else False,
        'score': 1 if correctness == 'correct' else 0,
        'msg': 'Your problem was graded {0}'.format(correctness)
    }

    # Set the fake xqueue server to always respond
    # correct/incorrect when asked to grade a problem
    world.xqueue.config['default'] = response_dict


@step(u'I answer a "([^"]*)" problem "([^"]*)ly"')
def answer_problem_step(step, problem_type, correctness):
    """ Mark a given problem type correct or incorrect, then submit it.

    *problem_type* is a string representing the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect']
    """
    # Change the answer on the page
    input_problem_answer(step, problem_type, correctness)

    # Submit the problem
    check_problem(step)


@step(u'I input an answer on a "([^"]*)" problem "([^"]*)ly"')
def input_problem_answer(_, problem_type, correctness):
    """
    Have the browser input an answer (either correct or incorrect)
    """
    assert correctness in ['correct', 'incorrect']
    assert problem_type in PROBLEM_DICT
    answer_problem(world.scenario_dict['COURSE'].number, problem_type, correctness)


@step(u'I check a problem')
def check_problem(step):
    # first scroll down so the loading mathjax button does not
    # cover up the Check button
    world.browser.execute_script("window.scrollTo(0,1024)")
    world.css_click("button.check")

    # Wait for the problem to finish re-rendering
    world.wait_for_ajax_complete()


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
    problem_has_answer(world.scenario_dict['COURSE'].number, problem_type, answer_class)


@step(u'I reset the problem')
def reset_problem(_step):
    world.css_click('button.reset')

    # Wait for the problem to finish re-rendering
    world.wait_for_ajax_complete()


@step(u'I press the button with the label "([^"]*)"$')
def press_the_button_with_label(_step, buttonname):
    button_css = 'button span.show-label'
    elem = world.css_find(button_css).first
    world.css_has_text(button_css, elem)
    world.css_click(button_css)


@step(u'The "([^"]*)" button does( not)? appear')
def action_button_present(_step, buttonname, doesnt_appear):
    button_css = 'div.action button[data-value*="%s"]' % buttonname
    if bool(doesnt_appear):
        assert world.is_css_not_present(button_css)
    else:
        assert world.is_css_present(button_css)


@step(u'the Show/Hide button label is "([^"]*)"$')
def show_hide_label_is(_step, label_name):
    # The label text is changed by static/xmodule_js/src/capa/display.js
    # so give it some time to change on the page.
    label_css = 'button.show span.show-label'
    world.wait_for(lambda _: world.css_has_text(label_css, label_name))


@step(u'I should see a score of "([^"]*)"$')
def see_score(_step, score):
    # The problem progress is changed by
    # cms/static/xmodule_js/src/capa/display.js
    # so give it some time to render on the page.
    score_css = 'div.problem-progress'
    expected_text = '({})'.format(score)
    world.wait_for(lambda _: world.css_has_text(score_css, expected_text))


@step(u'[Mm]y "([^"]*)" answer is( NOT)? marked "([^"]*)"')
def assert_answer_mark(_step, problem_type, isnt_marked, correctness):
    """
    Assert that the expected answer mark is visible
    for a given problem type.

    *problem_type* is a string identifying the type of problem (e.g. 'drop down')
    *correctness* is in ['correct', 'incorrect', 'unanswered']
    """
    # Determine which selector(s) to look for based on correctness
    assert correctness in ['correct', 'incorrect', 'unanswered']
    assert problem_type in PROBLEM_DICT

    # At least one of the correct selectors should be present
    for sel in PROBLEM_DICT[problem_type][correctness]:
        if bool(isnt_marked):
            world.wait_for(lambda _: world.is_css_not_present(sel))  # pylint: disable=cell-var-from-loop
            has_expected = world.is_css_not_present(sel)
        else:
            world.css_find(sel)  # css_find includes a wait_for pattern
            has_expected = world.is_css_present(sel)

        # As soon as we find the selector, break out of the loop
        if has_expected:
            break

    # Expect that we found the expected selector
    assert has_expected
