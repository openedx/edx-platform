from lettuce import world, step
from lettuce.django import django_url
from nose.tools import assert_equals, assert_in

@step('I navigate to an openended question$')
def navigate_to_an_openended_question(step):
    problem = '/courses/MITx/3.091x/2012_Fall/courseware/Week_10/Polymer_Synthesis/'
    world.browser.visit(django_url(problem))
    tab_css = 'ol#sequence-list > li > a[data-element="5"]'
    world.browser.find_by_css(tab_css).click()

@step(u'I enter the answer "([^"]*)"')
def enter_the_answer_text(step, text):
    textarea_css = 'textarea'
    world.browser.find_by_css(textarea_css).first.fill(text)

@step(u'I see the grader message "([^"]*)"$')
def see_grader_message(step, msg):
    message_css = 'div.external-grader-message'
    grader_msg = world.browser.find_by_css(message_css).text
    assert_in(msg, grader_msg)

@step(u'I see the grader status "([^"]*)"')
def see_the_grader_status(step, status):
    status_css = 'div.grader-status'
    grader_status = world.browser.find_by_css(status_css).text
    assert_equals(status, grader_status)

@step(u'I submit the answer "([^"]*)"$')
def i_submit_the_answer_text(step, text):
    textarea_css = 'textarea'
    world.browser.find_by_css(textarea_css).first.fill(text)
    check_css = 'input.check'
    world.browser.find_by_css(check_css).click()

@step(u'I visit the staff grading page$')
def i_visit_the_staff_grading_page(step):
    course_u = '/courses/MITx/3.091x/2012_Fall'
    world.browser.visit(django_url('%s/staff_grading' % course_u))

@step(u'my answer is queued for instructor grading')
def answer_is_queued_for_instructor_grading(step):
    assert False, 'This step must be implemented'