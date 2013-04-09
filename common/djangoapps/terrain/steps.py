#pylint: disable=C0111
#pylint: disable=W0621

# Disable the "wildcard import" warning so we can bring in all methods from
# course helpers and ui helpers
#pylint: disable=W0401

# Disable the "Unused import %s from wildcard import" warning
#pylint: disable=W0614

# Disable the "unused argument" warning because lettuce uses "step"
#pylint: disable=W0613

from lettuce import world, step
from .course_helpers import *
from .ui_helpers import *
from lettuce.django import django_url
from nose.tools import assert_equals, assert_in

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
    world.visit('/')
    assert world.is_css_present('header.global')


@step(u'I (?:visit|access|open) the dashboard$')
def i_visit_the_dashboard(step):
    world.visit('/dashboard')
    assert world.is_css_present('section.container.dashboard')


@step('I should be on the dashboard page$')
def i_should_be_on_the_dashboard(step):
    assert world.is_css_present('section.container.dashboard')
    assert world.browser.title == 'Dashboard'


@step(u'I (?:visit|access|open) the courses page$')
def i_am_on_the_courses_page(step):
    world.visit('/courses')
    assert world.is_css_present('section.courses')


@step(u'I press the "([^"]*)" button$')
def and_i_press_the_button(step, value):
    button_css = 'input[value="%s"]' % value
    world.css_click(button_css)


@step(u'I click the link with the text "([^"]*)"$')
def click_the_link_with_the_text_group1(step, linktext):
    world.click_link(linktext)


@step('I should see that the path is "([^"]*)"$')
def i_should_see_that_the_path_is(step, path):
    assert world.url_equals(path)


@step(u'the page title should be "([^"]*)"$')
def the_page_title_should_be(step, title):
    assert_equals(world.browser.title, title)


@step(u'the page title should contain "([^"]*)"$')
def the_page_title_should_contain(step, title):
    assert(title in world.browser.title)


@step('I log in$')
def i_log_in(step):
    world.log_in('robot', 'test')


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


@step(r'click (?:the|a) link (?:called|with the text) "([^"]*)"$')
def click_the_link_called(step, text):
    world.click_link(text)


@step(r'should see that the url is "([^"]*)"$')
def should_have_the_url(step, url):
    assert_equals(world.browser.url, url)


@step(r'should see (?:the|a) link (?:called|with the text) "([^"]*)"$')
def should_see_a_link_called(step, text):
    assert len(world.browser.find_link_by_text(text)) > 0


@step(r'should see "(.*)" (?:somewhere|anywhere) in (?:the|this) page')
def should_see_in_the_page(step, text):
    assert_in(text, world.css_text('body'))


@step('I am logged in$')
def i_am_logged_in(step):
    world.create_user('robot')
    world.log_in('robot', 'test')
    world.browser.visit(django_url('/'))


@step(u'I am an edX user$')
def i_am_an_edx_user(step):
    world.create_user('robot')


@step(u'User "([^"]*)" is an edX user$')
def registered_edx_user(step, uname):
    world.create_user(uname)
