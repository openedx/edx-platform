from lettuce import world, step
from lettuce.django import django_url
from nose.tools import assert_equals, assert_in
from logging import getLogger
logger = getLogger(__name__)

@step('I navigate to an openended question$')
def navigate_to_an_openended_question(step):
    world.register_by_course_id('MITx/3.091x/2012_Fall')
    world.log_in('robot@edx.org','test')
    problem = '/courses/MITx/3.091x/2012_Fall/courseware/Week_10/Polymer_Synthesis/'
    world.browser.visit(django_url(problem))
    tab_css = 'ol#sequence-list > li > a[data-element="5"]'
    world.browser.find_by_css(tab_css).click()

@step('I navigate to an openended question as staff$')
def navigate_to_an_openended_question_as_staff(step):
    world.register_by_course_id('MITx/3.091x/2012_Fall', True)
    world.log_in('robot@edx.org','test')
    problem = '/courses/MITx/3.091x/2012_Fall/courseware/Week_10/Polymer_Synthesis/'
    world.browser.visit(django_url(problem))
    tab_css = 'ol#sequence-list > li > a[data-element="5"]'
    world.browser.find_by_css(tab_css).click()

@step(u'I enter the answer "([^"]*)"$')
def enter_the_answer_text(step, text):
    textarea_css = 'textarea'
    world.browser.find_by_css(textarea_css).first.fill(text)

@step(u'I submit the answer "([^"]*)"$')
def i_submit_the_answer_text(step, text):
    textarea_css = 'textarea'
    world.browser.find_by_css(textarea_css).first.fill(text)
    check_css = 'input.check'
    world.browser.find_by_css(check_css).click()

@step('I click the link for full output$')
def click_full_output_link(step):
    link_css = 'a.full'
    world.browser.find_by_css(link_css).first.click()

@step(u'I visit the staff grading page$')
def i_visit_the_staff_grading_page(step):
    # course_u = '/courses/MITx/3.091x/2012_Fall'
    # sg_url = '%s/staff_grading' % course_u
    world.browser.click_link_by_text('Instructor')
    world.browser.click_link_by_text('Staff grading')    
    # world.browser.visit(django_url(sg_url))

@step(u'I see the grader message "([^"]*)"$')
def see_grader_message(step, msg):
    message_css = 'div.external-grader-message'
    grader_msg = world.browser.find_by_css(message_css).text
    assert_in(msg, grader_msg)

@step(u'I see the grader status "([^"]*)"$')
def see_the_grader_status(step, status):
    status_css = 'div.grader-status'
    grader_status = world.browser.find_by_css(status_css).text
    assert_equals(status, grader_status)

@step('I see the red X$')
def see_the_red_x(step):
    x_css = 'div.grader-status > span.incorrect'
    assert world.browser.find_by_css(x_css)

@step(u'I see the grader score "([^"]*)"$')
def see_the_grader_score(step, score):
    score_css = 'div.result-output > p'
    score_text = world.browser.find_by_css(score_css).text
    assert_equals(score_text, 'Score: %s' % score)

@step('I see the link for full output$')
def see_full_output_link(step):
    link_css = 'a.full'
    assert world.browser.find_by_css(link_css)

@step('I see the spelling grading message "([^"]*)"$')
def see_spelling_msg(step, msg):
    spelling_css = 'div.spelling'
    spelling_msg = world.browser.find_by_css(spelling_css).text    
    assert_equals('Spelling: %s' % msg, spelling_msg)

@step(u'my answer is queued for instructor grading$')
def answer_is_queued_for_instructor_grading(step):
    list_css = 'ul.problem-list > li > a'
    actual_msg = world.browser.find_by_css(list_css).text
    expected_msg = "(0 graded, 1 pending)"
    assert_in(expected_msg, actual_msg)
