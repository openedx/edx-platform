from lettuce import world, step
from lettuce.django import django_url


@step('I click on View Courseware')
def i_click_on_view_courseware(step):
    css = 'a.enter-course'
    world.browser.find_by_css(css).first.click()


@step('I click on the "([^"]*)" tab$')
def i_click_on_the_tab(step, tab_text):
    world.click_link(tab_text)
    world.save_the_html()

@step('I visit the courseware URL$')
def i_visit_the_course_info_url(step):
    url = django_url('/courses/MITx/6.002x/2012_Fall/courseware')
    world.browser.visit(url)


@step(u'I do not see "([^"]*)" anywhere on the page')
def i_do_not_see_text_anywhere_on_the_page(step, text):
    assert world.browser.is_text_not_present(text)


@step(u'I am on the dashboard page$')
def i_am_on_the_dashboard_page(step):
    assert world.browser.is_element_present_by_css('section.courses')
    assert world.browser.url == django_url('/dashboard')


@step('the "([^"]*)" tab is active$')
def the_tab_is_active(step, tab_text):
    assert world.css_text('.course-tabs a.active') == tab_text

@step('the login dialog is visible$')
def login_dialog_visible(step):
    assert world.css_visible('form#login_form.login_form')
