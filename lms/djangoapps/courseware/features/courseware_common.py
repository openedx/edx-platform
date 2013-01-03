from lettuce import world, step
from lettuce.django import django_url

@step('I click on View Courseware')
def i_click_on_view_courseware(step):
    css = 'p.enter-course'
    world.browser.find_by_css(css).first.click()

@step('I click on the "([^"]*)" tab$')
def i_click_on_the_tab(step, tab):
    world.browser.find_link_by_text(tab).first.click()
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
def the_tab_is_active(step, tab):
    css = '.course-tabs a.active'
    active_tab = world.browser.find_by_css(css)
    assert (active_tab.text == tab)

@step('the login dialog is visible$')
def login_dialog_visible(step):
    css = 'form#login_form.login_form'
    assert world.browser.find_by_css(css).visible
