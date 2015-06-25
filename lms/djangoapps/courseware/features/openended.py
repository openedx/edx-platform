# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

from lettuce import world, step
from lettuce.django import django_url
from nose.tools import assert_equals, assert_in  # pylint: disable=no-name-in-module
from logging import getLogger
logger = getLogger(__name__)


@step('I navigate to an openended question$')
def navigate_to_an_openended_question(step):
    world.register_by_course_key('MITx/3.091x/2012_Fall')
    world.log_in(email='robot@edx.org', password='test')
    problem = '/courses/MITx/3.091x/2012_Fall/courseware/Week_10/Polymer_Synthesis/'
    world.browser.visit(django_url(problem))
    tab_css = 'ol#sequence-list > li > a[data-element="5"]'
    world.css_click(tab_css)


@step('I navigate to an openended question as staff$')
def navigate_to_an_openended_question_as_staff(step):
    world.register_by_course_key('MITx/3.091x/2012_Fall', True)
    world.log_in(email='robot@edx.org', password='test')
    problem = '/courses/MITx/3.091x/2012_Fall/courseware/Week_10/Polymer_Synthesis/'
    world.browser.visit(django_url(problem))
    tab_css = 'ol#sequence-list > li > a[data-element="5"]'
    world.css_click(tab_css)


@step(u'I enter the answer "([^"]*)"$')
def enter_the_answer_text(step, text):
    world.css_fill('textarea', text)


@step(u'I submit the answer "([^"]*)"$')
def i_submit_the_answer_text(step, text):
    world.css_fill('textarea', text)
    world.css_click('input.check')


@step('I click the link for full output$')
def click_full_output_link(step):
    world.css_click('a.full')


@step(u'I visit the staff grading page$')
def i_visit_the_staff_grading_page(step):
    world.click_link('Instructor')
    world.click_link('Staff grading')


@step(u'I see the grader message "([^"]*)"$')
def see_grader_message(step, msg):
    message_css = 'div.external-grader-message'
    assert_in(msg, world.css_text(message_css))


@step(u'I see the grader status "([^"]*)"$')
def see_the_grader_status(step, status):
    status_css = 'div.grader-status'
    assert_equals(status, world.css_text(status_css))


@step('I see the red X$')
def see_the_red_x(step):
    assert world.is_css_present('div.grader-status > span.incorrect')


@step(u'I see the grader score "([^"]*)"$')
def see_the_grader_score(step, score):
    score_css = 'div.result-output > p'
    score_text = world.css_text(score_css)
    assert_equals(score_text, 'Score: %s' % score)


@step('I see the link for full output$')
def see_full_output_link(step):
    assert world.is_css_present('a.full')


@step('I see the spelling grading message "([^"]*)"$')
def see_spelling_msg(step, msg):
    spelling_msg = world.css_text('div.spelling')
    assert_equals('Spelling: %s' % msg, spelling_msg)


@step(u'my answer is queued for instructor grading$')
def answer_is_queued_for_instructor_grading(step):
    list_css = 'ul.problem-list > li > a'
    actual_msg = world.css_text(list_css)
    expected_msg = "(0 graded, 1 pending)"
    assert_in(expected_msg, actual_msg)
