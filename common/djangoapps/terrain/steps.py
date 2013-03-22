from lettuce import world, step
from .helpers import *
from lettuce.django import django_url
from nose.tools import assert_equals
import time

from logging import getLogger
logger = getLogger(__name__)


@step(u'I wait (?:for )?"(\d+)" seconds?$')
def wait(step, seconds):
    world.wait(seconds)

@step('I reload the page$')
def reload_the_page(step):
    world.browser.reload()


@step('I press the browser back button$')
def browser_back(step):
    world.browser.driver.back()


@step('I (?:visit|access|open) the homepage$')
def i_visit_the_homepage(step):
    world.browser.visit(django_url('/'))
    assert world.browser.is_element_present_by_css('header.global', 10)


@step(u'I (?:visit|access|open) the dashboard$')
def i_visit_the_dashboard(step):
    world.browser.visit(django_url('/dashboard'))
    assert world.browser.is_element_present_by_css('section.container.dashboard', 5)


@step('I should be on the dashboard page$')
def i_should_be_on_the_dashboard(step):
    assert world.browser.is_element_present_by_css('section.container.dashboard', 5)
    assert world.browser.title == 'Dashboard'


@step(u'I (?:visit|access|open) the courses page$')
def i_am_on_the_courses_page(step):
    world.browser.visit(django_url('/courses'))
    assert world.browser.is_element_present_by_css('section.courses')


@step(u'I press the "([^"]*)" button$')
def and_i_press_the_button(step, value):
    button_css = 'input[value="%s"]' % value
    world.browser.find_by_css(button_css).first.click()


@step(u'I click the link with the text "([^"]*)"$')
def click_the_link_with_the_text_group1(step, linktext):
    world.browser.find_link_by_text(linktext).first.click()


@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    assert world.browser.url == django_url(path)


@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert_equals(world.browser.title, title)


@step(u'the page title should contain "([^"]*)"$')
def the_page_title_should_contain(step, title):
    assert(title in world.browser.title)


@step('I am a logged in user$')
def i_am_logged_in_user(step):
    world.create_user('robot')
    world.log_in('robot', 'test')


@step('I am not logged in$')
def i_am_not_logged_in(step):
    world.browser.cookies.delete()


@step('I am staff for course "([^"]*)"$')
def i_am_staff_for_course_by_id(step, course_id):
    world.register_by_course_id(course_id, True)


@step('I log in$')
def i_log_in(step):
    world.log_in('robot', 'test')


@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    world.create_user('robot')
